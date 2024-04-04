from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import send_mail 
from bu import settings
from django.db.models import Max, Min


from .models import (Pay,
                     BannerImage, 
                     Product, 
                     Brand,
                     Category,
                     Order)

from asgiref.sync import sync_to_async

from random import choice
import json



def sizes(sizes: list) -> list:
    if sizes:
        sz = sorted(i for i in set(list(zip(*sizes))[0]) if (i.replace('.', '').replace(',', '').isdigit() or i.isalpha()))
        return sz
    else: return []


def convert_column_foreign_ids(temp: dict, **kwargs) -> list[dict]:
    temp['Категорія_id'] = kwargs['category'][temp['Категорія_id']]
    temp['Бренд_id'] = kwargs['brand'][temp['Бренд_id']]

    photos = [temp['first'], temp['second'], temp['third'], temp['fourth']]
    temp['photo'] = dict(zip(['tit', 'stit', 'static1', 'static2'], [photos[i] for i in range(len(photos)) if photos[i]]))
    temp['Розмір'] = temp['Розмір'].split(' ')

    return temp


async def get_pays_methods() -> list:
    request = await sync_to_async(Pay.objects.values_list)('method')

    return [i[0] for i in await sync_to_async(list)(request)]


async def get_banners() -> list:
    request = await sync_to_async(BannerImage.objects.values_list)('banner', 'link')

    return {i[0]: i[1] for i in await sync_to_async(list)(request)}


async def get_categories() -> dict:
    request = await sync_to_async(Category.objects.values)()
    to_list = await sync_to_async(list)(request)

    return {'category': {i['id']: i['Категорія'] for i in to_list},
            'reverse_category': {i['Категорія']: i['id'] for i in to_list}}


async def get_brands() -> dict:
    request = await sync_to_async(Brand.objects.values)()
    to_list = await sync_to_async(list)(request)

    return {'brand': {i['id']: i['Бренд'] for i in to_list},
            'reverse_brand': {i['Бренд']: i['id'] for i in to_list}}


async def get_products(fields: dict, **kwargs) -> dict:
    obj = Product.objects

    request = None
    if fields:
        request = await sync_to_async(obj.filter)(**fields)
    else:
        request = await sync_to_async(obj.all)()

    if 'sort' in kwargs:
        match kwargs['sort']:
            case 'min-sort':
                request = request.order_by('Ціна2')
            case 'max-sort':
                request = request.order_by('-Ціна2')
            case _:
                pass
    
    all_categories = await sync_to_async(list)(await sync_to_async(obj.values)('Категорія_id', 'id'))
    
    if 'Категорія_id' in fields:
        size = await sync_to_async(obj.filter)(Категорія_id=fields['Категорія_id'])
        size = await sync_to_async(list)(await sync_to_async(size.values)('Розмір'))
        
        brand = await sync_to_async(obj.filter)(Категорія_id=fields['Категорія_id'])
        brand = await sync_to_async(list)(await sync_to_async(brand.values)('Бренд_id'))
    else:
        size = await sync_to_async(list)(await sync_to_async(obj.values)('Розмір'))
        brand = await sync_to_async(list)(await sync_to_async(obj.values)('Бренд_id'))


    return {'cards': await sync_to_async(list)(request.values()), 
            'all_categories': all_categories, 
            'count': await sync_to_async(request.count)(),
            'sizes': sizes(i['Розмір'].split(' ') for i in size),
            'brand': brand}
        

async def get_max_min_price():
    obj = Product.objects

    min_price = await sync_to_async(obj.aggregate)(Min('Ціна2'))
    max_price = await sync_to_async(obj.aggregate)(Max('Ціна2'))

    return [min_price['Ціна2__min'], max_price['Ціна2__max']]


async def context(start: int = None, end: int = None, **kwargs):
    category = await get_categories()
    brand = await get_brands()
    
    field_category = {'Категорія_id': category['reverse_category'][kwargs['Категорія']] if 'Категорія' in kwargs else None}
    field_brand = {'Бренд_id': brand['reverse_brand'][kwargs['Бренд']] if 'Бренд' in kwargs else None}
    field_size = {'Розмір__regex': kwargs['Розмір'] if 'Розмір' in kwargs else None}
    field_prices = {k: v for k, v in kwargs.items() if k in ['Ціна2__gte', 'Ціна2__lte']} if 'Ціна2__gte' and 'Ціна2__lte' in kwargs else {}
    
    fields = {k: v for k, v in dict(field_category | field_brand | field_size).items() if v} | field_prices

    products = await get_products(fields, **kwargs)

    min_price, max_price = await get_max_min_price()

    data = {
        'oplata': await get_pays_methods(),
        'banner': await get_banners(),
        'category': set([category['category'][i['Категорія_id']] for i in products['all_categories']]),
        'category_' : dict([(category['category'][i['Категорія_id']], i['id']) for i in products['all_categories']]),
        'sizes': products['sizes'],
        'brands': set([brand['brand'][i['Бренд_id']] for i in products['brand']]),
        'min_price': min_price, 
        'max_price': max_price,
        'count': products['count'],
        'card' : [convert_column_foreign_ids(i, 
                                             category=category['category'],
                                             brand=brand['brand']) for i in products['cards'][start:end]]
    } 

    return await sync_to_async(set_context_categories)(data)


def set_context_categories(temp: dict) -> dict:
    temp['foot_category'] = {}
    category = list(temp['category']).copy()
    keys = 0

    while keys != 4:
        k = choice(category)

        temp['foot_category'][k] = Product.objects.get(id=temp['category_'][k]).first

        del category[category.index(k)]
        
        keys += 1

    return temp


async def get_page(temp: dict) -> int:
    return int(temp['page'][0]) if 'page' in temp else 1


async def price(temp: dict) -> list[int] | list[None]:
    return [int(temp['price-min'][0]), int(temp['price-max'][0])] if 'price-min' in temp and 'price-max' in temp else [None, None]


async def search(r):
    get = await sync_to_async(dict)(r.GET)
    page = await get_page(get)

    items_count = 12
    start = (page - 1) * items_count
    end = start + items_count


    db_r = {i: get[i][0] for i in get if get.keys()}

    price_min, price_max = await price(get)
    if price_min and price_max:
        db_r = db_r | {'Ціна2__gte': price_min, 'Ціна2__lte': price_max}

    cont = await context(start, end, **db_r)


    if 'sort' in get.keys():
        cont['sort'] = db_r['sort']

    
    total_pages = (cont['count'] + items_count - 1) // items_count
    cont['page'] = page
    cont['total_pages'] = total_pages

    return await sync_to_async(render)(r, 'pages/home.html', cont)



def get_orders(r):
    req = json.loads(r.body)

    try:
        c = list(filter(lambda x: Product.objects.get(id=int(x['idProduct'])), req))
        return JsonResponse({'status': 400, 'data': c})
    except:
        return JsonResponse({'status': 400, 'data': 'trash empty'})


async def product(r):
    product = int(r.GET['id'])

    cont = await context()
    cont['foot_cards'] = [choice(cont['card']) for _ in range(4)]

    cont['card'] = [i for i in cont['card'] if i['id'] == product][0]
    return await sync_to_async(render)(r, 'pages/product.html', cont)


async def info(r):
    con = await context()

    return await sync_to_async(render)(r, 'pages/info.html', con)


async def mail(
        client_email: str, 
        data: list[dict],
        subject: str = 'Дякуємо за замовлення в нашому магазиині!'
):
    ordw = []
    for i in data:

        product = await sync_to_async(Product.objects.get)(id=i.get("idProduct"))
        await sync_to_async(print)(product)
        await sync_to_async(ordw.append)([product, i.get("value"), i.get("ordersize")])

    products = "".join([
                    f"\tТовар номер - {ordw.index(i) + 1}\n" \
                    f"\t\tКатегорія - {i[0].Категорія}\n" \
                    f"\t\tБренд - {i[0].Бренд}\n" \
                    f"\t\tМодель - {i[0].Модель}\n" \
                    f"\t\tКолір - {i[0].Колір}\n" \
                    f"\t\tКількість - {i[1]}\n" \
                    f"\t\tРозмір - {i[2]}\n\n" for i in ordw
                ])
    
    await sync_to_async(send_mail)(
        subject="У вас нове замовлення!",
        message=f"Ім'я клієнта: {data[0].get('userName')} {data[0].get('secondName')}\n" \
                f"Номер телефону: {data[0].get('userPhone')}\n" \
                f"Пошта клієнта: {data[0].get('userEmail')}\n" \
                f"Місто та відділення: м. {data[0].get('City')}, {data[0].get('vidil')}\n" \
                f"Тип оплати: {data[0].get('opls')}\n" \
                "Товари:\n" \
                f"{products}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=settings.ORDERS_RECEPTIENS,
        fail_silently=False
    )

    await sync_to_async(send_mail)(
        subject=subject, 
        message="Ваше замовлення зарєстровано, "  \
                f"та буде доставлено у місто {data[0].get('City')}, " \
                f"відділення {data[0].get('vidil')}.\n" \
                "Інформація про товар:\n" \
                f"{products}",
        from_email=settings.DEFAULT_FROM_EMAIL, 
        recipient_list=[client_email],
        fail_silently=False
    )


async def order(r):
    try:
        req = await sync_to_async(json.loads)(r.POST['data'])
        order_ = {}

        for i in range(len(req)):

            order_['product_id'] = int(req[i]['idProduct'])
            order_['name'] = req[i]['userName']
            order_['second_name'] = req[i]['secondName']
            order_['phone'] = req[i]['userPhone']
            order_['email'] = req[i]['userEmail']
            order_['city'] = req[i]['City']
            order_['warhouse'] = req[i]['vidil']
            order_['pay'] = req[i]['opls']
            order_['count'] = req[i]['value']
            order_['size'] = req[i]['ordersize']

            await sync_to_async(Order.objects.create)(**order_)

        await mail(order_['email'], data=req)

        return JsonResponse({'status': 200})
    
    except Exception as e:
        print(e)
        return JsonResponse({'status': 400})