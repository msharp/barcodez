import falcon

from .resources import PingResource, FaviconResource
from .resources import SymbologyInfoResource, VersionInfoResource
from .resources import UrlBarcodeResource, JsonBarcodeResource

def create_app():
    api = app = falcon.API()

    app.add_route('/ping', PingResource())
    app.add_route('/favicon.ico', FaviconResource())

    app.add_route('/info/symbologies', SymbologyInfoResource())
    app.add_route('/info/versions', VersionInfoResource())

    app.add_route('/barcode/{symbology}', UrlBarcodeResource())
    app.add_route('/barcode/{symbology}/{data}', UrlBarcodeResource())
    app.add_route('/{encoded_json}', JsonBarcodeResource())

    return app
