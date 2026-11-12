#!/usr/bin/env python3
"""Soft, mystical UI sounds: glassy bells, warm pads and a little hall reverb (all synthesised, no samples)."""
import os, wave
import numpy as np

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app', 'gr8core', 'data')
SR = 44100
rng = np.random.default_rng(7)


def t(sec):
    return np.arange(int(SR * sec)) / SR


def at(sec, x, total):
    out = np.zeros(int(SR * total)); i = int(SR * sec)
    out[i:i + len(x)] += x[:len(out) - i]
    return out


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR); y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc; y[i] = acc
    return y


def bell(f, sec, decay=2.6, bright=0.9):
    """Soft glass bell: gentle FM, slightly detuned pair, quick fade-in so there is no click."""
    x = t(sec)
    idx = bright * np.exp(-x * 5)
    tone = sum(np.sin(2 * np.pi * f * d * x + idx * np.sin(2 * np.pi * f * 2.0 * x)) for d in (1.0, 1.0035)) / 2
    tone += 0.18 * np.sin(2 * np.pi * f * 2.76 * x) * np.exp(-x * 7)       # glassy upper partial
    env = np.exp(-x * decay) * np.minimum(1, x / 0.008)
    return tone * env


def pad(f, sec, attack=0.8):
    x = t(sec)
    tone = sum(np.sin(2 * np.pi * f * d * x + p) for d, p in ((1, 0), (1.004, 1.3), (.996, 2.1), (2.001, .4)))
    env = np.minimum(1, x / attack) * np.minimum(1, (sec - x) / (sec * .45))
    return lowpass(tone, 2200) * env / 4


def reverb(x, length=2.4, decay=.55, mix=.38):
    ir_t = t(length)
    ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t / decay)
    ir = lowpass(ir, 5200); ir[0] = 0
    wet = np.fft.irfft(np.fft.rfft(x, len(x) + len(ir)) * np.fft.rfft(ir, len(x) + len(ir)))[:len(x) + len(ir)]
    dry = np.concatenate([x, np.zeros(len(ir))]); wet = np.resize(wet, len(dry)) if len(wet) != len(dry) else wet
    wet = wet / (np.abs(wet).max() + 1e-9) * np.abs(x).max()
    return dry * (1 - mix) + wet * mix


def save(name, y, gain=.36):
    y = y / (np.abs(y).max() + 1e-9) * gain
    n = int(SR * .02); y[-n:] *= np.linspace(1, 0, n)                      # no click at the end
    with wave.open(os.path.join(D, name), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((y * 32767).astype('<i2').tobytes())


def boot():
    T = 3.2
    y = sum(at(0, pad(f, 3.0), T) for f in (146.83, 220.0, 329.63, 369.99)) * .9      # D maj9 swell
    for i, f in enumerate((587.33, 739.99, 880.0, 1108.73, 1318.51)):                # rising harp of bells
        y += at(.55 + i * .16, bell(f, 2.2, 2.2) * (.5 - i * .04), T)
    y += at(1.45, bell(1760.0, 1.6, 3.0, .5) * .18, T) + at(1.6, bell(2217.46, 1.4, 3.4, .4) * .12, T)   # shimmer
    save('boot.wav', reverb(y, 2.6, .7, .42)[:int(SR * 4.2)], .34)


def ok():
    T = 1.2
    y = at(0, bell(880.0, 1.1), T) + at(.13, bell(1318.51, 1.0), T) * .85 + at(.22, bell(2637.0, .7, 4, .3), T) * .15
    save('ok.wav', reverb(y, 1.8, .5, .35)[:int(SR * 2.0)], .3)


def error():
    """Gentle, not alarming: two warm low tones settling down a minor third, with a breath of air."""
    T = 1.2
    tone = lambda f, s: (np.sin(2 * np.pi * f * t(s)) + .25 * np.sin(4 * np.pi * f * t(s))) * \
        np.minimum(1, t(s) / .04) * np.exp(-t(s) * 3.2)
    air = lowpass(rng.standard_normal(int(SR * .7)), 900) * np.hanning(int(SR * .7)) * .5
    y = at(0, tone(329.63, 1.0), T) * .8 + at(.2, tone(277.18, 1.0), T) + at(0, air, T) * .35
    save('error.wav', reverb(lowpass(y, 1600), 1.8, .5, .35)[:int(SR * 2.0)], .28)


def card():
    T = .9
    y = sum(at(i * .065, bell(f, .8, 4.0, .6) * (1 - i * .15), T) for i, f in enumerate((1174.66, 1567.98, 2093.0)))
    save('card.wav', reverb(y, 1.4, .4, .32)[:int(SR * 1.5)], .26)


def tick():
    """A water-drop plip."""
    x = t(.18)
    f = 700 + 900 * np.exp(-x * 60)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 30) * np.minimum(1, x / .002)
    save('tick.wav', reverb(y, .8, .25, .25)[:int(SR * .6)], .2)


if __name__ == '__main__':
    boot(); ok(); error(); card(); tick()
    print('sounds written')
