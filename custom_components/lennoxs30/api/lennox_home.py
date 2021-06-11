import logging
import json

_LOGGER = logging.getLogger(__name__)

class lennox_home(object):

    id: int = None
    idx: int = None
    name: str = None
    json: json = None

    def __init__(self, homeId:int):
        self.id = homeId
        _LOGGER.info(f"Creating lennox_home  homeId [{self.id}]") 

    def update(self, homeIdx:int, homeName:str, json:json) -> None:
        self.idx = homeIdx
        self.name = homeName
        self.json = json
        _LOGGER.info(f"Updating lennox_home homeIdx [{str(self.idx)} homeId [{self.id}] homeName [{self.name}] json [{str(json)}]") 
