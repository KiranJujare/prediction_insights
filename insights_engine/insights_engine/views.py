import json

import collections
from collections import defaultdict

import operator
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render
from geopy.distance import vincenty

from models import run_query


def get_heatmap_obj(lat, long, count):
    return "{location: new google.maps.LatLng(%d, %d), weight: %d}" % (lat, long, count)


def get_sales_data(seller_id, field_name, field_value):
    if field_name and field_value:
        field_value = str(json.dumps(field_value.split(",")))[1:-1]
        query = "select ll.lat, ll.long, sum(od.count) from orders_data od, l_l_mapping ll where od.count>0 and ll.pincode = od.cx_address_pincode and seller_id = '%s' and %s in (%s) group by %s, ll.lat, ll.long" % (
        seller_id, field_name, field_value, field_name)
    else:
        query = "select ll.lat, ll.long, sum(od.count) from orders_data od, l_l_mapping ll where od.count>0 and ll.pincode = od.cx_address_pincode and seller_id = '%s' group by ll.lat, ll.long" % seller_id

    print query
    data = run_query(query)
    response = []
    for each in data:
        response.append({"lat": each[0], "long": each[1], "count": each[2]})
    return response


def get_demand_data(seller_id, field_name, field_value):
    if field_name and field_value:
        field_value = str(json.dumps(field_value.split(",")))[1:-1]
        query = "select ll.lat, ll.long, sum(od.count) from orders_data od, l_l_mapping ll where od.count>0 and ll.pincode = od.seller_pincode and seller_id = '%s' and %s in (%s) group by %s, ll.lat, ll.long " % (
        seller_id, field_name, field_value, field_name)
    else:
        query = "select ll.lat, ll.long, sum(od.count) from orders_data od, l_l_mapping ll where od.count>0 and ll.pincode = od.seller_pincode and seller_id = '%s' group by ll.lat, ll.long " % seller_id
    print query
    data = run_query(query)
    response = []
    for each in data:
        response.append({"lat": each[0], "long": each[1], "count": each[2]})
    return response


def index(request):
    seller_id = request.GET['seller']
    sales = get_sales_data(seller_id, None, None)
    demand = get_demand_data(seller_id, None, None)
    top_listings = get_default_top_listings(seller_id)
    wh_predictions_data = defaultdict(list)
    total_count = 0
    for each in sales:
        total_count+= each['count']
        fulfilment_model = get_warehouse_predictions(each['lat'], each['long'])
        if fulfilment_model in wh_predictions_data:
            wh_predictions_data[fulfilment_model] = wh_predictions_data.get(fulfilment_model) + each['count']
        else:
            wh_predictions_data[fulfilment_model] = each['count']
    for each in wh_predictions_data.keys():
        wh_predictions_data[each] = round((wh_predictions_data.get(each)/total_count)*100, 2)

    # sorted_x = sorted(wh_predictions_data.items(), key=operator.itemgetter(1))

    return render(request, 'index.html',
                  {"sales": sales, "demand": demand, "seller": seller_id, "top_listings": top_listings, "wh_predictions_data": wh_predictions_data})


def get_field_data(field_name, seller_id):
    data = run_query(
        "select %s from orders_data where seller_id = '%s' and %s is not null and %s != '' group by %s order by count(*) desc limit 200;" % (
        field_name, seller_id, field_name, field_name, field_name))
    response = []
    for each in data:
        response.append(each[0])
    return response


def get_by_field(request):
    field_name = request.GET['field_name']
    seller_id = request.GET['seller']
    field = ""
    if "product_id" == field_name:
        field = "FSN"
    if "listing_id" == field_name:
        field = "Listing"
    if "vertical" == field_name:
        field = "Vertical"
    return HttpResponse(
        json.dumps({"data": get_field_data(field_name, seller_id), "field": field}, cls=DjangoJSONEncoder),
        content_type="application/json")


def get_lat_long_by_field(request):
    field_name = request.GET['field']
    field_value = request.GET['field_value']
    seller_id = request.GET['seller']

    if "FSN" == field_name:
        field = "product_id"
    if "Listing" == field_name:
        field = "listing_id"
    if "Vertical" == field_name:
        field = "vertical"

    sales = get_sales_data(seller_id, field, field_value)
    demand = get_demand_data(seller_id, field, field_value)

    return render(request, 'index.html', {"sales": sales, "demand": demand, "seller": seller_id, "field": field_name})


def get_default_top_listings(seller_id):
    data = run_query(
        "select listing_id, round((count(listing_id) / (select count(*) from orders_data where seller_id = '%s')) * 100, 2) as percentage from orders_data where seller_id = '%s' group by listing_id order by count(*) desc limit 10;" % (
        seller_id, seller_id))
    response = []
    for each in data:
        response.append({"listing_id": each[0], "percentage": each[1]})
    return response


def get_warehouse():
    return [['Delhi Warehouse', 28.545723, 77.087084],
            ['Delhi Gurgaon 1 Warehouse', 28.459585, 77.009950],
            ['Bilaspur Warehouse', 28.293493, 76.885802],
            ['Bilaspur Pataudi 1 Warehouse', 28.327572, 76.776988],
            ['Ghaziabad Warehouse', 28.662222, 77.443361],
            ['Lucknow01warehouse', 26.792291, 80.979062],
            ['Jaipur Mini FC Sitapur', 26.778634, 75.835320],
            ['Mumbai Chembur 1 Warehouse', 19.025671, 72.887387],
            ['Mumbai Bhiwandi Warehouse', 19.374957, 73.093994],
            ['Hyderabad Medchal 01', 17.635991, 78.503905],
            ['Bangalore Whitefield Warehouse', 13.005984, 77.766092],
            ['Bangalore HSR Micro Warehouse', 12.910586, 77.641831],
            ['Bangalore Jigani 1 Warehouse', 12.780932, 77.627015],
            ['Chennai01Warehouse', 13.156448, 80.130996],
            ['Kolkata Warehouse', 22.654326, 88.539681],
            ['Kolkata Dankuni 1 Warehouse', 22.733065, 88.314389]]


def get_warehouse_predictions(lat, long, distance=200):
    nearest_wh = {}
    for each_wh in get_warehouse():
        wh_coordinates = (each_wh[1], each_wh[2])
        delivery_coordinates = (lat, long)
        if vincenty(wh_coordinates, delivery_coordinates).kilometers < distance:
            nearest_wh[vincenty(wh_coordinates, delivery_coordinates).kilometers] = each_wh[0]

    collections.OrderedDict(sorted(nearest_wh.items()))
    if nearest_wh.keys().__len__() > 0:
        return nearest_wh[nearest_wh.keys()[0]]
    else:
        return "Non FBF"
