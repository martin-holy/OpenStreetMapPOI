import os
import json
import math
import datetime
import requests

class POI:
  def __init__(self, lat, lon, km, tags):
    self.tags = tags
    self.apiUrl = 'https://overpass-api.de/api/interpreter?data='
    self.bbox = self.getBoundingBox(lat, lon, km)

    # change working directory to current file directory
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

  def getBoundingBox(self, pLatitude, pLongitude, pDistanceInKm):
    latRadian = math.radians(pLatitude)

    degLatKm = 110.574235
    degLongKm = 110.572833 * math.cos(latRadian)
    deltaLat = pDistanceInKm / degLatKm
    deltaLong = pDistanceInKm / degLongKm

    minLat = pLatitude - deltaLat
    minLong = pLongitude - deltaLong
    maxLat = pLatitude + deltaLat
    maxLong = pLongitude + deltaLong

    return f'{minLat},{minLong},{maxLat},{maxLong}'

  def assembleUrl(self):
    # build query
    query = []
    for tag in self.tags.keys():
      query.append(f'node[{tag}];')

    # assemble url
    self.url = f'{self.apiUrl}[out:json][timeout:25][bbox:{self.bbox}];({"".join(query)});out;'

  def download(self):
    self.assembleUrl()
    print('Downloading POI ...')
    response = requests.get(self.url)
    self.poi = response.json()['elements']

    # for debug
    #with open('poi.json', 'r', encoding='utf-8') as poiJson:
    #  self.poi = json.load(poiJson)['elements']

    print(f'{len(self.poi)} POI downloaded.')

  def filter(self):
    ids = []
    if os.path.exists("poi.ids"):
      with open('poi.ids', 'r') as poiIds:  
        ids = poiIds.read().split(',')
    
    found = 0
    poiFiltered = []
    for poi in self.poi:
      id = str(poi['id'])
      if id in ids:
        found += 1
        continue
      poiFiltered.append(poi)
      ids.append(id)

    with open('poi.ids', 'w') as poiIds:
      poiIds.write(','.join(ids))

    print(f'Filtered out {found} POI')

    self.poi = poiFiltered

  def parse(self):
    print('Parsing POI ...')
    for poi in self.poi:
      tags = poi['tags']
      desc = []
      icon = ''
      nameKey = 'name' if 'name' in tags else ''
      
      for k, v in tags.items():
        desc.append(f'{k}: {v}')

        if icon == '' and f'{k}={v}' in self.tags:
          icon = self.tags[f'{k}={v}']
          if nameKey == '':
            nameKey = k

      poi['desc'] = '\n'.join(desc)
      poi['icon'] = icon
      poi['name'] = tags[nameKey]

  def save(self):
    print('Saving POI ...')
    with open(f'{datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.gpx', 'w', encoding='utf-8') as poiGpx:
      poiGpx.write(f'<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
      poiGpx.write(f'<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1" xmlns:locus="http://www.locusmap.eu">\n')
      for poi in self.poi:
        poiGpx.write(f'<wpt lat="{poi["lat"]}" lon="{poi["lon"]}"><name>{poi["name"]}</name><sym>{poi["icon"]}</sym>')
        poiGpx.write(f'<extensions><locus:icon>file:OpenStreetMapPOI-icons.zip:{poi["icon"]}.png</locus:icon></extensions>')
        poiGpx.write(f'<desc><![CDATA[{poi["desc"]}]]></desc>')
        poiGpx.write('</wpt>\n')
      poiGpx.write('</gpx>')
    print(f'{len(self.poi)} POI saved.\n')

# Tags (key=value) and Icon names
tags = {
  "natural=spring": "spring",
  "natural=hot_spring": "hot_spring",
  "natural=cave_entrance": "cave",
  "natural=waterfall": "waterfall",
  "natural=peak": "peak",
  "sport=climbing": "climbing",
  "drinking_water=yes": "drinking_water",
  "drinking_water=no": "drinking_water",
  "amenity=drinking_water": "drinking_water",
  "amenity=fountain": "fountain",
  "amenity=bbq": "bbq",
  "historic=ruins": "ruins",
  "historic=mine_shaft": "mine",
  "historic=mine": "mine",
  "historic=tomb": "cave",
  "historic=castle": "castle",
  "historic=archaeological_site": "archaeological_site",
  "tourism=viewpoint": "viewpoint",
  "tourism=picnic_site": "picnic_site",
  "man_made=adit": "mine",
  "man_made=mineshaft": "mine",
  "man_made=mine": "mine"
}

# lat, lng, km, tags
poi = POI(40.017, -0.25, 7, tags)
poi.download()
poi.filter()
poi.parse()
poi.save()
