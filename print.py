#!/usr/bin/env python
from serial import Serial
from serial.tools import list_ports
from time import sleep
from math import log

DOTS = 6
HEAT_TIME = 180
HEAT_INTERVAL = 127
PRINT_DENSITY = 0b001
PRINT_BREAK_TIME = 0b00011

EMPH = 0b00001000
TALL = 0b00010000
WIDE = 0b00100000

def printer_config(s):
    s.write(bytearray([
        27,
        55,
        DOTS,
        HEAT_TIME,
        HEAT_INTERVAL,
    ]))
    s.write(bytearray([
        18,
        35,
        (PRINT_DENSITY << 5) | PRINT_BREAK_TIME,
    ]))

def im_row(width):
    """note: width is in bytes (x8 pixels)"""
    if (width <= 0):
        raise ValueError('row must be at least 1 byte wide')
    if (width > 48):
        raise ValueError('width: {} -- can only print rows up to 48 bytes (384px) wide'.format(
            width))
    return bytearray([
        0x12,  # [DC2]
        ord('*'),
        1,  # height
        width
    ])

def print_im(im, ser):
    dots = 12
    heatTime = 255
    heatInterval = 127
    ser.write([
        27,
        55,
        dots,
        heatTime,
        heatInterval,
    ])

    printDensity = 0b111
    printBreakTime = 0b00111
    ser.write([
        18,
        35,
        (printDensity << 5) | printBreakTime,
    ])

    channels = len(im.getpixel((0, 0)))
    for y in range(im.size[1]):
        out = list(ROW)
        for xi in range(0, im.size[0], 8):
            b = 0
            for i in range(8):
                b <<= 1
                px = im.getpixel((xi + i, y))
                black = px[3] > 127 and sum(px[:3]) < 384
                b |= black
            out.append(b)
        ser.write(out)
        sleep(0.034)


def print_break(ser, n=2):
    ser.write('\n' * n);

def title(t, s, n=2):
    print_break(s, 1)

    if n == 1:
        s.write([27, '!', EMPH | TALL | WIDE])
    elif n == 2:
        s.write([27, 'a', 1])  # center
        s.write([27, '!', EMPH])  # bold
        s.write([29, 'B', 1])  # invert
    else:
        s.write([27, 'a', 1])  # center
 
    s.write(' {} \n'.format(t))

    s.write([27, '!', 0])  # unformat    
    s.write([29, 'B', 0])  # uninvert
    s.write([27, 'a', 0])  # left

    print_break(s, 1)


CHUNK_SIZE = 800
def text(t, s):
    whole_chunks = len(t) // CHUNK_SIZE  # max 800 characters at a time
    for i in range(whole_chunks):
        s.write(t[i * CHUNK_SIZE:(i+1) * CHUNK_SIZE])
        sleep(0.005 * CHUNK_SIZE)
    remainders = len(t) % CHUNK_SIZE
    if remainders > 0:
        s.write(t[whole_chunks * CHUNK_SIZE:])
    sleep(0.005 * remainders)


def do_stuff(s):
    printer_config(s)

    title('DFT bin octave\nintervals', s, 1)

    text('''\
Octave: a doubling of frequency.

Human pitch perception fits a
log scale, and has repetitive
qualities every octave.

Discrete fourier transforms
(DFT) operate on a linear
frequency scale. The scales
don't match!

If you express the frequency bin
width of a DFT in terms of
the octaves it takes up on a
more-human log scale, you get
this expression:
''', s)

    title(' log2(2i + 1) - log2(2i - 1) ', s)

    text('''\
where 'i' is the bin index (bin
0 is the DC offset).

This relation between bin number
and octave interval is

  *independent of sample rate
       and number of bins*

which is weird and cool! It
feels like maybe some kind of
basic truth about DFTs.

Here are the intervals in terms
of octaves and semitones of the
first 127 bin widths of any DFT:

bin    octaves    semitones
  0       -           -
{}
'''.format('\n'.join('{i:3d}   {o:8.7f}   {s:9.7f}'.format(
    i=i,
    o=log(2*i+1,2)-log(2*i-1, 2),
    s=(log(2*i+1,2)-log(2*i-1, 2))*12) for i in range(1, 128))), s)

    print_break(s, 4)


if __name__ == '__main__':
    import sys
    try:
        port = sys.argv[1]
    except IndexError:
        maybes = list(list_ports.grep('usb'))
        if len(maybes) == 0:
            sys.stderr.write('missing serial port (probably /dev/tty.usbserial-something)\n')
            sys.exit(1)
        if len(maybes) > 1:
            sys.stderr.write('not sure which serial port to use. likely candidates:\n{}\n'.format(
                '\n'.join(map(lambda m: '{}\t{}\t{}'.format(m.device, m.description, m.manufacturer), maybes))))
            sys.exit(1)
        port = maybes[0].device
    s = Serial(port, 19200)
    sleep(0.3)

    do_stuff(s)

    sleep(0.3)
    s.close()
