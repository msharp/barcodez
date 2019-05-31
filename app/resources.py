import sys
import re
import base64
import binascii
import json

import falcon
import zint

from .barcode import Barcode, BarcodeGenerationError, IGNORE_ZINT_CONSTS


def available_symbologies():
    """
    There are multiple available symbologies filter out the items from the
    dir() which are not actual barcode constants
    """
    consts = [d[8:] for d in dir(zint) if d.startswith('BARCODE_')]

    return [d for d in consts if d not in IGNORE_ZINT_CONSTS]


def get_zint_symbology(symbology):
    """
    Interpet the symbology parameter
    """
    s = symbology.upper()
    if s in available_symbologies():
        return eval(f'zint.BARCODE_{s}')
    else:
        raise TypeError


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


class JsonBarcodeResource:
    """
    This resource accepts a JSON object as a Bese64 encoded string
    """
    def on_get(self, req, resp, encoded_json):
        try:
            json_data = base64.urlsafe_b64decode(encoded_json)
            bc_data = json.loads(json_data)

            # accept 'type' key for backwards compatability
            bc_symbol_type = bc_data.get('symbology') or bc_data['type']
            symbology = get_zint_symbology(bc_symbol_type.upper())
            data = bc_data['data']

        except (binascii.Error, json.decoder.JSONDecodeError):
            raise falcon.HTTPBadRequest(description="Bad data")
        except KeyError:
            raise falcon.HTTPBadRequest(description="Some fields missing")

        try:
            with Barcode(symbology, data) as bc:
                bc.show_text = bc_data.get('text', False)
                bc.width = bc_data.get('width')
                bc.height = bc_data.get('height')

                resp.content_type = 'image/png'
                resp.stream = bc.barcode()

        except BarcodeGenerationError:
            raise falcon.HTTPError(status='500 Server Error')


class UrlBarcodeResource:
    """
    This resource supports describing the barcode via URL schema
    """
    def on_get(self, req, resp, symbology, data=None):
        try:
            symbology = get_zint_symbology(symbology)
        except TypeError:
            raise falcon.HTTPError(status='404 Not Found',
                                   description="Invalid symbology")

        if not data:
            try:
                data = req.params['data']
            except KeyError:
                raise falcon.HTTPMissingParam('data')

        try:
            with Barcode(symbology, data) as bc:
                bc.show_text = bool_from_params(req.params.get('text'))
                bc.width = req.params.get('width')
                bc.height = req.params.get('height')

                resp.content_type = 'image/png'
                resp.stream = bc.barcode()

        except BarcodeGenerationError:
            raise falcon.HTTPError(status='500 Server Error')


class VersionInfoResource:
    def on_get(self, req, resp):
        versions = {
            'python-zint': zint.__version__,
            'zintlib': re.sub('0', '.', str(zint.ZBarcode_Version())),
            'python': "{}.{}.{}".format(*sys.version_info),
            'pillow': PIL.__version__
        }

        resp.content_type = 'application/json'
        resp.media = {'versions': versions}


class SymbologyInfoResource:
    def on_get(self, req, resp):
        symbologies = available_symbologies()
        symbologies.sort()

        resp.content_type = 'application/json'
        resp.media = {'symbologies': symbologies}


class FaviconResource:
    def on_get(self, req, resp):
        symbology = get_zint_symbology('QRCODE')
        with Barcode(symbology, 'favicon.ico') as bc:
            bc.width = 28
            bc.height = 28
            resp.content_type = 'image/png'
            resp.stream = bc.barcode()


class PingResource:
    def on_get(self, req, resp):
        resp.content_type = 'text/plain'
        resp.body = 'PONG'
        resp.status = falcon.HTTP_200
