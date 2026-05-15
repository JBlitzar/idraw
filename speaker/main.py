from __future__ import annotations

import argparse
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import mido
import serial
from serial.tools import list_ports


DEFAULT_MIDI_PATH = Path(__file__).with_name("ode_to_joy.mid")


@dataclass(frozen=True)
class NoteEvent:
    t: float  # seconds
    note: int
    on: bool


class EBB:
    """Minimal EBB (EiBotBoard) serial client.

    We only use a tiny subset of the protocol:
    - SM (stepper move / timed delay)
    - EM (enable motors / set microstep mode)
    - ES (e-stop)
    - V  (version query) [optional]

    References:
    https://evil-mad.github.io/EggBot/ebb.html
    """

    def __init__(self, port: str, *, baudrate: int = 115200, timeout_s: float = 0.25):
        self._ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout_s,
            write_timeout=timeout_s,
        )
        # Many EBB-like devices reset on serial open.
        time.sleep(2.0)
        self._ser.reset_input_buffer()
        self._ser.reset_output_buffer()

    @property
    def port(self) -> str:
        return str(self._ser.port)

    def close(self) -> None:
        try:
            self._ser.close()
        except Exception:
            pass

    def _write_line(self, line: str) -> None:
        if not line.endswith("\r"):
            line += "\r"
        self._ser.write(line.encode("ascii", errors="strict"))

    def _read_available_lines(self, max_lines: int = 50) -> list[str]:
        lines: list[str] = []
        for _ in range(max_lines):
            raw = self._ser.readline()
            if not raw:
                break
            lines.append(raw.decode("ascii", errors="replace").strip())
        return [ln for ln in lines if ln != ""]

    def drain_input(self, *, max_bytes: int = 65536) -> None:
        """Non-blocking read/discard of any pending serial input.

        Some firmware/configs may emit a reply per command (e.g. future syntax mode).
        If the host never reads those bytes, buffers can fill and stall streaming.
        """

        try:
            waiting = int(getattr(self._ser, "in_waiting", 0) or 0)
        except Exception:
            waiting = 0
        if waiting <= 0:
            return
        to_read = min(waiting, max_bytes)
        try:
            self._ser.read(to_read)
        except Exception:
            pass

    def version(self) -> str | None:
        # Legacy firmware returns a single line with the version string.
        self._write_line("V")
        lines = self._read_available_lines(max_lines=5)
        return lines[0] if lines else None

    def set_ok_responses(self, enabled: bool) -> None:
        # CU,1,0 disables the trailing OK response in legacy syntax mode.
        # If firmware is in future syntax mode, this may have no effect.
        self._write_line(f"CU,1,{1 if enabled else 0}")
        # Read and discard any immediate reply.
        self._read_available_lines(max_lines=5)

    def e_stop(self, disable_motors: bool = True) -> None:
        self._write_line(f"ES,{1 if disable_motors else 0}")
        self._read_available_lines(max_lines=5)

    def enable_motors(
        self, *, microstep_mode: int = 1, motor2_enable: int | None = 1
    ) -> None:
        """Enable motors and set microstep mode.

        microstep_mode:
          0: disable motor 1
          1: enable motor 1, set global step mode 1/16 (default)
          2: 1/8
          3: 1/4
          4: 1/2
          5: full step
        motor2_enable:
          0 disables motor 2, nonzero enables motor 2.
        """

        if motor2_enable is None:
            self._write_line(f"EM,{microstep_mode}")
        else:
            self._write_line(f"EM,{microstep_mode},{motor2_enable}")
        self._read_available_lines(max_lines=5)

    def disable_motors(self) -> None:
        self._write_line("EM,0,0")
        self._read_available_lines(max_lines=5)

    def sm(self, duration_ms: int, steps1: int, steps2: int = 0) -> None:
        if duration_ms <= 0:
            raise ValueError("duration_ms must be > 0")
        self._write_line(f"SM,{duration_ms},{steps1},{steps2}")


def _autodetect_ebb_port() -> str | None:
    ports = list(list_ports.comports())
    if not ports:
        return None

    def score(p: list_ports.ListPortInfo) -> int:
        text = " ".join(
            [
                p.device or "",
                p.description or "",
                p.manufacturer or "",
                p.product or "",
                p.interface or "",
                p.hwid or "",
            ]
        ).lower()
        s = 0
        if "eibot" in text or "ebb" in text:
            s += 50
        if "axidraw" in text:
            s += 50
        if "usbmodem" in text or "usbserial" in text or "acm" in text:
            s += 10
        if "cp210" in text or "ftdi" in text:
            s += 5
        return s

    ranked = sorted(ports, key=score, reverse=True)
    best = ranked[0]
    if score(best) <= 0:
        return None

    # If the top choice is clearly better than the runner-up, pick it.
    if len(ranked) == 1:
        return best.device
    if score(ranked[0]) >= score(ranked[1]) + 20:
        return best.device
    return None


def _list_ports() -> str:
    ports = list(list_ports.comports())
    if not ports:
        return "(no serial ports found)"
    lines: list[str] = []
    for p in ports:
        extra = ", ".join(x for x in [p.description, p.manufacturer] if x)
        if extra:
            lines.append(f"- {p.device}  ({extra})")
        else:
            lines.append(f"- {p.device}")
    return "\n".join(lines)


def _note_to_hz(note: int) -> float:
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def _parse_midi_note_events(midi_path: Path) -> tuple[list[NoteEvent], float]:
    mid = mido.MidiFile(midi_path)
    tempo = 500000  # default 120 BPM

    events: list[NoteEvent] = []
    t_s = 0.0
    for msg in mido.merge_tracks(mid.tracks):
        t_s += mido.tick2second(msg.time, mid.ticks_per_beat, tempo)

        if msg.type == "set_tempo":
            tempo = msg.tempo
            continue

        if msg.type == "note_on":
            if msg.velocity == 0:
                events.append(NoteEvent(t=t_s, note=int(msg.note), on=False))
            else:
                events.append(NoteEvent(t=t_s, note=int(msg.note), on=True))
        elif msg.type == "note_off":
            events.append(NoteEvent(t=t_s, note=int(msg.note), on=False))

    events.sort(key=lambda e: e.t)
    end_time = events[-1].t if events else 0.0
    return events, end_time


def _pick_notes(active: dict[int, int], *, polyphony: int) -> list[int]:
    if not active:
        return []
    notes = sorted(active.keys())
    if polyphony <= 1:
        return [notes[-1]]
    return notes[-polyphony:]


def play_midi_on_plotter(
    *,
    midi_path: Path,
    port: str,
    segment_ms: int,
    polyphony: int,
    max_step_rate_hz: float,
    max_steps_per_half_segment: int,
    microstep_mode: int,
    motor2_enabled: bool,
    dry_run: bool,
) -> None:
    if segment_ms < 8:
        raise ValueError("segment_ms must be >= 8 ms (safety + EBB throughput)")
    if segment_ms % 2 != 0:
        segment_ms += 1

    half_ms = segment_ms // 2
    half_s = half_ms / 1000.0

    events, end_time_s = _parse_midi_note_events(midi_path)
    # Add a short tail so the last note has time to decay.
    total_time_s = end_time_s + 0.25

    if dry_run:
        print(f"MIDI: {midi_path}")
        print(f"Duration: {total_time_s:.2f} s (+tail)")
        print(f"Segments: {math.ceil(total_time_s / (segment_ms / 1000.0))}")
        return

    ebb = EBB(port)
    try:
        ver = ebb.version()
        if ver:
            print(f"EBB: {ver}")
        else:
            print("EBB: (no version response)")

        # Reduce serial chatter for streaming.
        ebb.set_ok_responses(enabled=False)

        # Put motors in a known microstep mode; enable motor 2 only if needed.
        ebb.enable_motors(
            microstep_mode=microstep_mode, motor2_enable=1 if motor2_enabled else 0
        )

        active: dict[int, int] = {}
        idx = 0
        seg_s = segment_ms / 1000.0
        n_segments = int(math.ceil(total_time_s / seg_s))

        t0 = time.monotonic()
        for seg_i in range(n_segments):
            seg_start_s = seg_i * seg_s
            # Apply all events up to this segment start.
            while idx < len(events) and events[idx].t <= seg_start_s:
                ev = events[idx]
                if ev.on:
                    active[ev.note] = active.get(ev.note, 0) + 1
                else:
                    if ev.note in active:
                        new_count = active[ev.note] - 1
                        if new_count <= 0:
                            del active[ev.note]
                        else:
                            active[ev.note] = new_count
                idx += 1

            notes = _pick_notes(active, polyphony=polyphony)

            if not notes:
                ebb.sm(segment_ms, 0, 0)
            else:
                # Map up to 2 voices onto the two stepper channels.
                # Polyphony > 2 is intentionally not supported (EBB has 2 stepper outputs).
                hz_1 = min(_note_to_hz(notes[0]), max_step_rate_hz)
                hz_2 = 0.0
                if len(notes) >= 2 and motor2_enabled:
                    hz_2 = min(_note_to_hz(notes[1]), max_step_rate_hz)

                steps1 = int(round(hz_1 * half_s))
                steps2 = int(round(hz_2 * half_s))

                steps1 = max(
                    -max_steps_per_half_segment, min(max_steps_per_half_segment, steps1)
                )
                steps2 = max(
                    -max_steps_per_half_segment, min(max_steps_per_half_segment, steps2)
                )

                # If rounding made a step count zero, you won't get a tone.
                if steps1 == 0 and steps2 == 0:
                    ebb.sm(segment_ms, 0, 0)
                else:
                    ebb.sm(half_ms, steps1, steps2)
                    ebb.sm(half_ms, -steps1, -steps2)

                    # Drain any firmware replies without blocking.
                    ebb.drain_input()

            # Keep real-time pacing; avoid FIFO overrun.
            target = t0 + (seg_i + 1) * seg_s
            now = time.monotonic()
            if now < target:
                time.sleep(target - now)

    except KeyboardInterrupt:
        print("\nInterrupted; stopping motors...")
        try:
            ebb.e_stop(disable_motors=True)
        except Exception:
            pass
    finally:
        try:
            ebb.disable_motors()
        except Exception:
            pass
        ebb.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Play a MIDI file on an AxiDraw/EBB plotter by driving the stepper motors like a speaker. "
            "Default behavior is monophonic: always play the lowest currently-held note."
        )
    )
    parser.add_argument(
        "--midi",
        type=Path,
        default=DEFAULT_MIDI_PATH,
        help="Path to MIDI file (default: speaker/ode_to_joy.mid)",
    )
    parser.add_argument(
        "--port",
        type=str,
        default=None,
        help="Serial port (e.g. /dev/cu.usbmodemXXXX). If omitted, attempts auto-detect.",
    )
    parser.add_argument(
        "--segment-ms",
        type=int,
        default=20,
        help="Control update interval in ms (must be even; default: 20).",
    )
    parser.add_argument(
        "--polyphony",
        type=int,
        default=1,
        choices=[1, 2],
        help="1 = mono (lowest note). 2 = two-voice (two lowest notes) mapped onto the two motors.",
    )
    parser.add_argument(
        "--max-step-rate-hz",
        type=float,
        default=2500.0,
        help="Safety cap on step rate in steps/sec (also caps pitch). Default: 2500.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=25,
        help="Safety cap on |steps| per half-segment to limit motion amplitude. Default: 25.",
    )
    parser.add_argument(
        "--microstep-mode",
        type=int,
        default=1,
        choices=[1, 2, 3, 4, 5],
        help="EBB global microstep mode: 1=1/16, 2=1/8, 3=1/4, 4=1/2, 5=full. Default: 1.",
    )
    parser.add_argument(
        "--no-motor2",
        action="store_true",
        help="Disable motor 2 output (forces mono on motor 1).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse MIDI and print timing info without touching hardware.",
    )
    args = parser.parse_args(argv)

    midi_path: Path = args.midi
    if not midi_path.exists():
        print(f"MIDI file not found: {midi_path}", file=sys.stderr)
        return 2

    port = args.port or _autodetect_ebb_port()
    if not port and not args.dry_run:
        print("Could not auto-detect an EBB/AxiDraw serial port.", file=sys.stderr)
        print("Available ports:", file=sys.stderr)
        print(_list_ports(), file=sys.stderr)
        print("\nRe-run with --port /dev/cu.usbmodemXXXX", file=sys.stderr)
        return 2

    if args.dry_run:
        play_midi_on_plotter(
            midi_path=midi_path,
            port="(dry-run)",
            segment_ms=args.segment_ms,
            polyphony=args.polyphony,
            max_step_rate_hz=args.max_step_rate_hz,
            max_steps_per_half_segment=args.max_steps,
            microstep_mode=args.microstep_mode,
            motor2_enabled=not args.no_motor2,
            dry_run=True,
        )
        return 0

    print(f"Using port: {port}")
    play_midi_on_plotter(
        midi_path=midi_path,
        port=port,
        segment_ms=args.segment_ms,
        polyphony=args.polyphony,
        max_step_rate_hz=args.max_step_rate_hz,
        max_steps_per_half_segment=args.max_steps,
        microstep_mode=args.microstep_mode,
        motor2_enabled=not args.no_motor2,
        dry_run=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
