from fastapi import FastAPI, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

client = MongoClient('mongodb://localhost:27017/')
db = client['water_tanks']

class Profile(BaseModel):
    username: str
    role: str
    color: str

class Tank(BaseModel):
    location: str
    lat: float
    long: float

class TankResponse(BaseModel):
    id: str
    location: str
    lat: float
    long: float

def get_profile_collection():
    return db['profile']

def get_tanks_collection():
    return db['tanks']

@app.get('/profile')
async def get_profile(profile_collection=Depends(get_profile_collection)):
    return profile_collection.find_one({}, {'_id': 0}) or {}

@app.post('/profile', response_model=dict)
async def create_profile(profile: Profile, profile_collection=Depends(get_profile_collection)):
    profile_data = jsonable_encoder(profile)
    profile_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result = profile_collection.insert_one(profile_data)
    return {"id": str(result.inserted_id), **profile_data}

@app.get('/tank', response_model=list[TankResponse])
async def get_tanks(tanks_collection=Depends(get_tanks_collection)):
    return list(tanks_collection.find({}, {'_id': 0}))

@app.get('/tank/{id}', response_model=TankResponse)
async def get_tank(id: str, tanks_collection=Depends(get_tanks_collection)):
    tank = tanks_collection.find_one({"_id": id}, {'_id': 0})
    if tank:
        return tank
    raise HTTPException(status_code=404, detail="Tank not found")

@app.post('/tank', response_model=TankResponse)
async def create_tank(tank: Tank, tanks_collection=Depends(get_tanks_collection)):
    tank_data = jsonable_encoder(tank)
    tank_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result = tanks_collection.insert_one(tank_data)
    return {"id": str(result.inserted_id), **tank_data}

@app.patch('/tank/{id}', response_model=TankResponse)
async def update_tank(id: str, updated_data: Tank, tanks_collection=Depends(get_tanks_collection)):
    tank = tanks_collection.find_one({"_id": id}, {'_id': 0})
    if not tank:
        raise HTTPException(status_code=404, detail="Tank not found")
    updated_data = jsonable_encoder(updated_data)
    updated_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    tanks_collection.update_one({"_id": id}, {"$set": updated_data})
    return {"id": id, **updated_data}

@app.delete('/tank/{id}', status_code=204)
async def delete_tank(id: str, tanks_collection=Depends(get_tanks_collection)):
    result = tanks_collection.delete_one({"_id": id})
    if result.deleted_count != 1:
        raise HTTPException(status_code=404, detail="Tank not found")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
