from bs4 import BeautifulSoup
import requests as req
import json
import os
import pandas
from decimal import *

class CadastralParcel:
    # Получение адресов по кадастровым номерам 
    def get_adres_cadastral_parcel(self, cadastral_parcel_numbers):
        url = ''
        adres = ''
        soup = ''
        dict_cadastral_parcel = {}
        # Перебираем кадастровые номера
        for cadastral_parcel in cadastral_parcel_numbers:
            # Заменяем : на - для запроса на сайт
            cadastral_parcel_dash = cadastral_parcel.replace(':','-')
            dict_cadastral_parcel[cadastral_parcel] = {}
            # Сохраняем кадастровый номер через дефис для названий файлов
            dict_cadastral_parcel[cadastral_parcel]['cadastral_parcel_dash'] = cadastral_parcel_dash
            url = f"https://kadastrmap.com/reestr/{cadastral_parcel_dash}/"
            adres = req.get(url)
            soup = BeautifulSoup(adres.text, "html.parser")
            result_soup = soup.title.text
            # Убираем лишние данные из полученного адресса и сохраняем в словарь
            if cadastral_parcel in result_soup:
                result_soup = result_soup.replace(cadastral_parcel, '')
            if " || KadastrMap.ru" in result_soup:
                dict_cadastral_parcel[cadastral_parcel]['adres'] = result_soup.replace(" || KadastrMap.ru", '')
            else:
                dict_cadastral_parcel[cadastral_parcel]['adres'] = result_soup
        
        return dict_cadastral_parcel
    # Изменение адресов кадастровых участков
    def data_conversion(self, dict_cadastral_parcel):
        
        for key in dict_cadastral_parcel.keys():
            dict_cadastral_parcel[key]['adres'] = dict_cadastral_parcel[key]['adres'].replace(" ", "+")

        return dict_cadastral_parcel
    # Получение координат через geocode-maps
    def yandex_api_get_coordinates(self, dict_cadastral, api_key):
        string_to_json = ''
        envelope = ''
        
        for key in dict_cadastral.keys():
            url_yandex_api_geocode = f"https://geocode-maps.yandex.ru/1.x/?apikey={api_key}&format=json&geocode={dict_cadastral[key]['adres']}"
            result_get_api = req.get(url_yandex_api_geocode).text
            string_to_json = json.loads(result_get_api)
            # Получаем координаты из результата запроса и сохраняем их
            envelope = string_to_json["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["boundedBy"]["Envelope"]
            center = string_to_json["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]['pos']
            dict_cadastral[key]['coordinates'] = envelope
            dict_cadastral[key]['coordinates']['pos'] = center

        return dict_cadastral
    # Отрисовка полигонов на изображениях со спутника
    def yandex_api_polygon_by_coordinates(self, dict_data):
        current_dir = os.getcwd()
        result_folder = 'result'
        # Создаем путь, где будут храниться изображения
        path = f"{current_dir}{os.sep}{result_folder}{os.sep}"
        # Проверка на существованеи пути
        if os.path.exists(path):
            pass
        else:
            os.mkdir(path)

        getcontext().prec = 6

        for key in dict_data.keys():
            # Получаем координаты нижнего и верхнего угла и центра  
            lower_corner = dict_data[key]['coordinates']['lowerCorner'].split(" ")
            upper_corner = dict_data[key]['coordinates']['upperCorner'].split(" ")
            center_coordinate = dict_data[key]['coordinates']['pos'].split(" ")
            #Расчитываем координаты полигона
            difference_x = (Decimal(upper_corner[0]) - Decimal(lower_corner[0]))/Decimal(16)
            difference_y = (Decimal(upper_corner[1]) - Decimal(lower_corner[1]))/Decimal(10)
            leftLowerCorner = f"{Decimal(center_coordinate[0]) - difference_x},{Decimal(center_coordinate[1]) - difference_y}"
            leftUpperCorner = f"{Decimal(center_coordinate[0]) - difference_x},{Decimal(center_coordinate[1]) + difference_y}"
            rightUpperCorner = f"{Decimal(center_coordinate[0]) + difference_x},{Decimal(center_coordinate[1]) + difference_y}"
            rightLowerCorner = f"{Decimal(center_coordinate[0]) + difference_x},{Decimal(center_coordinate[1]) - difference_y}"
            # Формируем строку координат для запроса Static API
            polygon_coordinates = f"{leftLowerCorner},{leftUpperCorner},{rightUpperCorner},{rightLowerCorner},{leftLowerCorner}"
            url_yandex_api_static = f"https://static-maps.yandex.ru/1.x/?l=sat&pt={center_coordinate[0]},{center_coordinate[1]},flag&pl={polygon_coordinates}"
            result_api_static = req.get(url_yandex_api_static)
            # Сохраняем картинку по созданному пути с именем кадастрового номера через дефис
            out = open(f"{path}{dict_data[key]['cadastral_parcel_dash']}.jpg", "wb")
            out.write(result_api_static.content)
            out.close()
        # Возвращаем путь для вывода в консоль
        return path

    # Функция старта выполнения скрипта
    def start_test_task(self, cadastral_parcel_numbers, api_key):
        # Получение словаря, содержащий адреса полученные по кадастровым номерам
        result_get_adres_cadastral_parcel = self.get_adres_cadastral_parcel(cadastral_parcel_numbers)
        # Изменение адрес для работы с апи 
        result_data_conversion = self.data_conversion(result_get_adres_cadastral_parcel)
        # Получение координат углов для отрисовки полигона
        result_yandex_api_get_coordinates = self.yandex_api_get_coordinates(result_data_conversion, api_key)
        # Отрисовка полигонов на изображениях со спутника
        path_result = self.yandex_api_polygon_by_coordinates(result_yandex_api_get_coordinates)

        return print(f"Программа выполнена успешно! Результат работы находится в {path_result}")


if __name__ == "__main__":
    # Чтение файла excel для получения списка кадастровых номеров 
    excel_data_df = pandas.read_excel('CadastralParcel.xlsx')
    # Cписок кадастровых номеров для получения изображений участков
    cadastral_parcel_numbers = excel_data_df['Cadastral parcel'].tolist()
    # API Geocode Яндекс.Краты
    api_key = "0ec2675a-e31e-42ea-8acc-fded64e0ec86"
    objectCadastralParcel = CadastralParcel()
    # Запускаем работу скрипта, передавая список кадастровых номеро и api ключ
    objectCadastralParcel.start_test_task(cadastral_parcel_numbers, api_key)
