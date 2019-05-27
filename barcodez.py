import io

import falcon

import zint # v1.1 from github; requires libzint >=2.6.0
import png
import PIL
from PIL import Image

IGNORE_ZINT_CONSTS = ['STDOUT','NO_ASCII','BIND','BOX','DOTTY_MODE']


def available_symbologies():
    """
    there are multiple available symbologies
    filter out the items from the dir() which
    are not actual barcode constants
    """
    consts = [d[8:] for d in dir(zint) if d.startswith('BARCODE_')]

    return [d for d in consts if d not in IGNORE_ZINT_CONSTS]

def get_zint_symbology(symbology):
    """
    interpet the symbology parameter
    """
    s = symbology.upper()
    if s in available_symbologies():
        return eval(f'zint.BARCODE_{s}')
    else:
        return None

def bool_from_params(param):
    """
    Accept 1, 0, (F|f)alse, (T|t)rue as boolean options default state is False
    """
    try:
        return bool(int(param))
    except ValueError:
        return param.lower() == 'true'
    except TypeError:
        return False

class Barcode:
    """
    class to manage the generation of barcode images

    usage:
    ```
    with Barcode(symbology, data) as bc:
        bc.width = 375
        bc.height = 95
        bc.show_text = True
        barcode = bc.barcode()
    ```
    """

    def __init__(self, symbology, data, width=None, height=None, show_text=False):

        self.symbology = symbology
        self.data = data

        self.width = width
        self.height = height
        self.show_text = show_text

    def barcode(self):
        """
        generate the barcode object and
        resize if required
        """
        self._generate_symbol()

        img = self._get_png_image()

        if self.width or self.height:
            if not self.width:
                self.width = self.symbol.contents.bitmap_width
            if not self.height:
                self.height = self.symbol.contents.bitmap_height

            img = self._resize(img)

        return img

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f" exc_type = {exc_type}; exc_val = {exc_val}; exc_tb = {exc_tb}")
        self._destroy_symbol()

    ### "private" methods ###

    def _get_pixel_map(self):
        """
        translate the bitmap bytes
        into black or white pixel values
        arranged in rows
        """
        bitmap = zint.bitmapbuf(self.symbol)

        pixel = 0
        frame = []
        for y in range(self.symbol.contents.bitmap_height):
            line = []
            for x in range(self.symbol.contents.bitmap_width):
                # Each pixel represented by a 3 byte RGB value
                if ord(bitmap[pixel]) > 0:
                    line.append(1) # white
                else:
                    line.append(0) # black
                pixel += 3
            frame.append(line)

        return frame

    def _get_png_image(self):
        """
        turn a 2D list of zeroes and ones
        into a greyscale PNG image
        stored in a BytesIO object
        """
        frame = self._get_pixel_map()

        barcode = io.BytesIO()
        writer = png.Writer(self.symbol.contents.bitmap_width,
                            self.symbol.contents.bitmap_height,
                            greyscale=True,
                            bitdepth=1)
        writer.write(barcode, frame)
        barcode.seek(0) # reset read cursor

        return barcode

    def _generate_symbol(self):
        """
        the pyzint library is a thin python wrapper
        over the zint C library and uses a similar API
        """
        self.symbol = zint.ZBarcode_Create()
        self.symbol.contents.symbology = self.symbology
        self.symbol.contents.show_hrt = self.show_text

        inp = zint.instr(bytes(self.data, 'utf-8'))

        err = zint.ZBarcode_Encode_and_Buffer(self.symbol, inp, 0, 0)
        if err != 0:
            errmsg = 'error: {}'.format(self.symbol.contents.errtxt)
            # FIXME raise something else here
            raise falcon.HTTPBadRequest(errmsg)


    def _destroy_symbol(self):
        """clean up"""
        try:
            zint.ZBarcode_Delete(self.symbol)
        except AttributeError:
            pass # no symbol present

    def _resize(self, barcode):
        """
        open the image (a BytesIO object)
        and resize using PIL/pillow
        resave into a new BytesIO object
        """
        img = Image.open(barcode)

        rszd = img.resize((int(self.width), int(self.height)), PIL.Image.LANCZOS)

        out = io.BytesIO()
        rszd.save(out, format='png')
        out.seek(0)

        return out


class BarcodesResource:

    def on_get(self, req, resp, symbology, data=None):

        symbology = get_zint_symbology(symbology)
        if not data:
            data = req.params['data']

        with Barcode(symbology, data) as bc:
            bc.show_text = bool_from_params(req.params.get('text'))
            bc.width = req.params.get('width')
            bc.height = req.params.get('height')

            resp.content_type = 'image/png'
            resp.stream = bc.barcode()

class InfoResource:
    def on_get(self, req, resp):
        resp.content_type = 'application/json'
        symbologies = available_symbologies()
        symbologies.sort()
        resp.media = {'symbologies': symbologies}

class FaviconResource:
    def on_get(self, req, resp):
        symbology = get_zint_symbology('QRCODE')
        with Barcode(symbology, 'favicon.ico') as bc:
            bc.width = 28
            bc.height = 28
            resp.content_type = 'image/png'
            resp.stream = bc.barcode()


# run this with `gunicorn app:api`
api = falcon.API()
api.add_route('/info/symbologies', InfoResource())
api.add_route('/favicon.ico', FaviconResource())

api.add_route('/{symbology}', BarcodesResource())
api.add_route('/{symbology}/{data}', BarcodesResource())
