from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse, HttpRequest
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from rest_framework.request import Request
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from property.models import Property
from property.serializers import PropertySerializer


# Create your views here.
@csrf_exempt
@api_view(['GET', 'POST', 'DELETE'])
def property_list_api(request: Request):
    rightmove_id = request.query_params.get('rightmove_id')
    if request.method == 'GET':
        if rightmove_id is None:
            items = Property.objects.all()
        else:
            items = Property.objects.filter(rightmove_id=rightmove_id).all()
        serializer = PropertySerializer(items, many=True)
        return JsonResponse(serializer.data, safe=False)
    
    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = PropertySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)
    
    elif request.method == 'DELETE':
        property_list = Property.objects.all()
        for item in property_list:
            item.delete()
        return HttpResponse(status=204) 
    
    return JsonResponse({
        'message': 'Unsupported method.'
    }, status=500)


@csrf_exempt
@api_view(['GET', 'PUT', 'DELETE'])
def property_detail_api(request: Request, pk):
    try:
        item = Property.objects.get(pk=pk)
    except Property.DoesNotExist:
        return HttpResponse(status=404)
    
    if request.method  == 'GET':
        serializer = PropertySerializer(item)
        return JsonResponse(serializer.data)
    
    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = PropertySerializer(item, data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)
    
    elif request.method == 'DELETE':
        item.delete()
        return HttpResponse(status=204)


def index(request: HttpRequest):
    if request.method == 'GET':
        offset = int(request.GET.get('offset', 20))
        page = int(request.GET.get('page', 1))
        if offset < 10:
            return redirect(to=f'/?offset={offset}&page={page}')
        property_all = Property.objects.order_by("-baths", "distance", "type_name").all()
        paginator = Paginator(property_all, offset)
        if page > paginator.num_pages:
            return redirect(to=f'/?offset={offset}&page={paginator.num_pages}')
        elif page < 1:
            return redirect(to=f'/?offset={offset}&page=1')
        else:
            return render(request, 'property/index.html', {
                'page': paginator.page(page),
                'paginator': paginator,
                'page_range': paginator.get_elided_page_range(page),
            })
    
    return HttpResponseNotAllowed(['GET'])
    