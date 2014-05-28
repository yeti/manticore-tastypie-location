from django.conf import settings
from googleplaces import GooglePlaces, ranking
from tastypie import http, fields
from tastypie.authorization import Authorization
from tastypie.bundle import Bundle
from tastypie.exceptions import BadRequest
from manticore_tastypie_core.manticore_tastypie_core.resources import ManticoreModelResource, ManticoreResource
from manticore_tastypie_user.manticore_tastypie_user.authentication import ExpireApiKeyAuthentication
from .models import Location


class GooglePlace(object):
    def __init__(self, id=None, name=None, address=None):
        self.id = id
        self.name = name
        self.address = address


class GooglePlaceResource(ManticoreResource):
    id = fields.CharField(attribute='id')
    name = fields.CharField(attribute='name')
    address = fields.CharField(attribute='vicinity', null=True)
    latitude = fields.FloatField()
    longitude = fields.FloatField()

    class Meta:
        resource_name = 'place'
        allowed_methods = ['get']
        object_class = GooglePlace
        authorization = Authorization()
        authentication = ExpireApiKeyAuthentication()
        always_return_data = True
        object_name = "place"

    def dehydrate_latitude(self, bundle):
        return bundle.obj.geo_location['lat']

    def dehydrate_longitude(self, bundle):
        return bundle.obj.geo_location['lng']

    def _client(self):
        return GooglePlaces(settings.GOOGLE_API_KEY)

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.id
        else:
            kwargs['pk'] = bundle_or_obj['id']

        return kwargs

    def get_object_list(self, bundle, **kwargs):
        latitude = bundle.request.GET.get('latitude')
        longitude = bundle.request.GET.get('longitude')

        if latitude and longitude:
            lat_lng = {"lat": latitude, "lng": longitude}
        else:
            raise BadRequest("Need latitude and longitude")

        query_name = bundle.request.GET.get('query', "")
        if query_name != "":
            query = self._client().text_search(query=query_name, radius=None)
        else:
            query = self._client().nearby_search(sensor=True, lat_lng=lat_lng, radius=8000)

        return query.places

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle, **kwargs)

    def obj_get(self, request=None, **kwargs):
        result = self._client().get_place(kwargs['pk'])
        result.get_details()
        return result


class LocationResource(ManticoreModelResource):
    class Meta:
        queryset = Location.objects.all()
        allowed_methods = ['get', 'post']
        authorization = Authorization()
        authentication = ExpireApiKeyAuthentication()
        resource_name = "location"
        object_name = "location"
        filtering = {
            'id': ['exact'],
            'name': ['exact'],
            'neighborhood': ['exact'],
            'city': ['exact'],
            'state': ['exact'],
            'country_code': ['exact', 'iexact'],
        }