p = """1203918203124+12312489124 # arbitrary p"""

def s():
    t = """p = %r

def s():
    t = %r
    exec(p)
    print(t %% (p, t), end='')

s()
"""
    exec(p)
    print(t % (p, t), end='')

s()