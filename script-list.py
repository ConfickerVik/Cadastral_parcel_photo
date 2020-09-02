from bs4 import BeautifulSoup
import requests as req
import string
import json

class CadastralParcel:
     
    def get_adres_cadastral_parcel(self, cadastral_parcel_numbers):
        url = ''
        adres = ''
        soup = ''
        adres_cadastral_parcel = []

        for cadastral_parcel in cadastral_parcel_numbers:
            url = f"https://kadastrmap.com/reestr/{cadastral_parcel.replace(':','-')}/"
            adres = req.get(url)
            soup = BeautifulSoup(adres.text, "html.parser")
            result_soup = soup.title.text

            if cadastral_parcel in result_soup:
                result_soup = result_soup.replace(cadastral_parcel, '')
            if " || KadastrMap.ru" in result_soup:
                adres_cadastral_parcel.append(result_soup.replace(" || KadastrMap.ru", ''))
            else:
                adres_cadastral_parcel.append(result_soup)
        
        return adres_cadastral_parcel

    def data_conversion(self, adres_list):
        list_adres_conversion = []

        for adres in adres_list:
            list_adres_conversion.append(adres.replace(" ", "+"))

        return list_adres_conversion

    def yandex_api_get_coordinates(self, list_data_conversion, api_key):
        coordinates_cadastral_parcel = []
        string_to_json = ''
        envelope = ''
        #point = ''
            
        for data in list_data_conversion:
            url_yandex_api_geocode = f"https://geocode-maps.yandex.ru/1.x/?apikey={api_key}&format=json&geocode={data}"
            result_get_api = req.get(url_yandex_api_geocode).text
            string_to_json = json.loads(result_get_api)
            envelope = string_to_json["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["boundedBy"]["Envelope"]
            #point = string_to_json["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]
            coordinates_cadastral_parcel.append(envelope)

        return coordinates_cadastral_parcel

    def yandex_api_polygon_by_coordinates(self, list_coordinates):
        i = 1
        for coordinates in list_coordinates:
            lower_corner = coordinates["lowerCorner"].split(" ")
            upper_corner = coordinates["upperCorner"].split(" ")
            polygon_coordinates = f"{lower_corner[0]},{lower_corner[1]},{upper_corner[0]},{lower_corner[1]},{upper_corner[0]},{upper_corner[1]},{lower_corner[0]},{upper_corner[1]},{lower_corner[0]},{lower_corner[1]}"
            url_yandex_api_static = f"https://static-maps.yandex.ru/1.x/?l=sat&pl={polygon_coordinates}"
            result_api_static = req.get(url_yandex_api_static)
            out = open(f"result\{i}.jpg", "wb")
            out.write(result_api_static.content)
            out.close()
            i += 1
        

    def start_test_task(self, cadastral_parcel_numbers, api_key):
        result_get_adres_cadastral_parcel = self.get_adres_cadastral_parcel(cadastral_parcel_numbers)
        result_data_conversion = self.data_conversion(result_get_adres_cadastral_parcel)
        result_yandex_api_get_coordinates = self.yandex_api_get_coordinates(result_data_conversion, api_key)
        self.yandex_api_polygon_by_coordinates(result_yandex_api_get_coordinates)
        #print(json.dumps(result_yandex_api_get_coordinates[0], indent=4))

        return "Программа выполнила работу!!!"


if __name__ == "__main__":

    cadastral_parcel_numbers = ["77:01:0001034:1071","54:35:101256:17","03:24:011204:11","38:36:000012:4033","02:55:010830:13"]
    api_key = "0ec2675a-e31e-42ea-8acc-fded64e0ec86"
    objectCadastralParcel = CadastralParcel()
    objectCadastralParcel.start_test_task(cadastral_parcel_numbers, api_key)
    #print(objectCadastralParcel.start_test_task(cadastral_parcel_numbers, api_key))
