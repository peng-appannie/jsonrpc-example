from flask import Flask
from flask_jsonrpc import JSONRPC
import json

from core.base import BaseDTO
from core.fields import String, Int, Bool, List, Dict

from protocols import DTOJsonEncoder, DTOJsonDecoder
from protocols import aa_data_api

from errors import APIError

class Category(BaseDTO):
    market = String()
    category_id = Int()
    is_main_category = Bool()
    legacy_category_id = Int()
    unified_categories = List(element_type=Int(), can_be_empty=True)
    localized_info = Dict(can_be_none=True)

app = Flask(__name__)

app.json_encoder = DTOJsonEncoder
app.json_decoder = DTOJsonDecoder

jsonrpc = JSONRPC(app, '/api')



@jsonrpc.method('get_categories')
@aa_data_api
def get_categories(id, name):
    category = Category(
        market='ios',
        category_id=100,
        is_main_category=False,
        legacy_category_id=1,
        unified_categories=[1,2,3],
        localized_info={'name': '123', 'value': {'z': 2, 'c': [12,3,4], 'd': False}}
    )
    return [category]


@jsonrpc.method('get_custom_error')
@aa_data_api
def test_custom_error():
    raise APIError(403, 'This is a custom error')

@jsonrpc.method('get_system_error')
@aa_data_api
def test_system_error():
    raise 'system error'


'''
import json
import app
from core.base import DTOJsonEncoder

c = app.Category(market='ios',category_id=100,is_main_category=False,legacy_category_id=1,unified_categories=[1,2,3],localized_info={'name': '123', 'value': {'z': 2, 'c': [12,3,4], 'd': False}})


json.dumps(c, cls=DTOJsonEncoder)

curl -i -X POST -H "Content-Type: application/json; indent=4" -d '{"jsonrpc": "2.0","method": "get_system_error","params": {}, "id": "1"}' http://127.0.0.1:5000/api
'''
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
    
