import argparse
import os
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom 
import yaml

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Konwertuje dane z jednego formatu na inny (XML, JSON, YAML)."
    )

    parser.add_argument(
        "input_file",
        type=str,
        help="Ścieżka do pliku wejściowego (np. input.xml, data.json)."
    )

    parser.add_argument(
        "output_file",
        type=str,
        help="Ścieżka do pliku wyjściowego (np. output.json, result.yaml)."
    )

    args = parser.parse_args()

    input_path = args.input_file
    output_path = args.output_file

    if not os.path.exists(input_path):
        parser.error(f"Plik wejściowy '{input_path}' nie istnieje.")

    _, input_ext = os.path.splitext(input_path)
    _, output_ext = os.path.splitext(output_path)

    input_format = input_ext[1:].lower() if input_ext else None
    output_format = output_ext[1:].lower() if output_ext else None

    allowed_formats = ['xml', 'json', 'yml', 'yaml']

    if input_format not in allowed_formats:
        parser.error(f"Nieobsługiwany format pliku wejściowego: '{input_ext}'. Oczekiwano: {', '.join(allowed_formats)}")
    if output_format not in allowed_formats:
        parser.error(f"Nieobsługiwany format pliku wyjściowego: '{output_ext}'. Oczekiwano: {', '.join(allowed_formats)}")

    if input_format == 'yml':
        input_format = 'yaml'
    if output_format == 'yml':
        output_format = 'yaml'

    return {
        "input_path": input_path,
        "input_format": input_format,
        "output_path": output_path,
        "output_format": output_format
    }


def read_and_validate_data(file_path, file_format):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_format == 'json':
                data = json.load(f)
                print(f"  Pomyślnie wczytano i zweryfikowano JSON z '{file_path}'.")
                return data
            elif file_format == 'xml':
                tree = ET.parse(f)
                root = tree.getroot()
                print(f"  Pomyślnie wczytano i zweryfikowano XML z '{file_path}'.")
                return root
            elif file_format == 'yaml':
                data = yaml.safe_load(f)
                print(f"  Pomyślnie wczytano i zweryfikowano YAML z '{file_path}'.")
                return data
            else:
                raise ValueError(f"Nieobsługiwany format dla wczytywania: {file_format}")
    except FileNotFoundError:
        print(f"Błąd: Plik '{file_path}' nie został znaleziony.")
        return None
    except (json.JSONDecodeError, ET.ParseError, yaml.YAMLError) as e:
        print(f"Błąd składni w pliku '{file_path}' ({file_format.upper()}): {e}")
        return None
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd podczas wczytywania '{file_path}': {e}")
        return None

def write_data_to_json(data, output_path):
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"  Pomyślnie zapisano dane do pliku JSON: '{output_path}'.")
        return True
    except TypeError as e:
        print(f"Błąd: Dane nie mogą być serializowane do JSON. Upewnij się, że to słownik/lista: {e}")
        return False
    except Exception as e:
        print(f"Wystąpił błąd podczas zapisu do pliku JSON '{output_path}': {e}")
        return False

def convert_dict_to_xml_element(tag, d):
   
    elem = ET.Element(tag)
    if isinstance(d, dict):
        for key, val in d.items():
            if isinstance(val, (dict, list)):
                child_elem = convert_dict_to_xml_element(key, val)
                elem.append(child_elem)
            else:
                child_elem = ET.SubElement(elem, key)
                child_elem.text = str(val)
    elif isinstance(d, list):
        
        for item in d:
          
            if isinstance(item, dict):
                
                child_elem = ET.SubElement(elem, tag[:-1] if tag.endswith('s') else tag) # heurystyka: usuń 's' z nazwy tagu listy
                for k, v in item.items():
                    if isinstance(v, (dict, list)):
                        sub_child = convert_dict_to_xml_element(k, v)
                        child_elem.append(sub_child)
                    else:
                        sub_child = ET.SubElement(child_elem, k)
                        sub_child.text = str(v)
            else:
                child_elem = ET.SubElement(elem, tag[:-1] if tag.endswith('s') else tag)
                child_elem.text = str(item)
    else:
        elem.text = str(d)
    return elem

def write_data_to_xml(data, output_path):
    try:
        if isinstance(data, ET.Element):
        
            root = data
        elif isinstance(data, (dict, list)):
            
            if isinstance(data, dict):
                root = convert_dict_to_xml_element("root", data)
            elif isinstance(data, list):
                root = ET.Element("root")
                for item in data:
                   
                    item_elem = convert_dict_to_xml_element("item", item)
                    root.append(item_elem)

        else:
            raise TypeError(f"Nieobsługiwany typ danych do zapisu do XML: {type(data)}")

        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml_as_string = reparsed.toprettyxml(indent="  ")

        with open(output_path, 'w', encoding='utf-8') as f:
           
            f.write(pretty_xml_as_string)
        print(f"  Pomyślnie zapisano dane do pliku XML: '{output_path}'.")
        return True
    except TypeError as e:
        print(f"Błąd: Dane nie mogą być skonwertowane lub serializowane do XML: {e}")
        return False
    except Exception as e:
        print(f"Wystąpił błąd podczas zapisu do pliku XML '{output_path}': {e}")
        return False


if __name__ == "__main__":
    try:
        parsed_args = parse_arguments()
        print(f"Pomyślnie sparsowano argumenty:")
        print(f"  Plik wejściowy: {parsed_args['input_path']} (Format: {parsed_args['input_format']})")
        print(f"  Plik wyjściowy: {parsed_args['output_path']} (Format: {parsed_args['output_format']})")

        print("\nRozpoczynanie wczytywania i walidacji pliku wejściowego...")
        input_data = read_and_validate_data(
            parsed_args['input_path'],
            parsed_args['input_format']
        )

        if input_data is not None:
            print("Walidacja pliku wejściowego zakończona sukcesem.")

            data_to_write = input_data 

            if parsed_args['output_format'] == 'json':
                print("\nRozpoczynanie zapisu danych do pliku JSON...")
                if isinstance(data_to_write, ET.Element):
                    print("  Konwersja XML (ElementTree) do JSON przed zapisem...")
                    
                    print("  Pomięto konwersję XML do JSON w tym etapie. Nie można zapisać.")
                    exit(1) 
                elif isinstance(data_to_write, (dict, list)):
                    write_success = write_data_to_json(data_to_write, parsed_args['output_path'])
                    if not write_success:
                        print("Program zakończył działanie z błędami podczas zapisu.")
                        exit(1)
            elif parsed_args['output_format'] == 'xml':
                print("\nRozpoczynanie zapisu danych do pliku XML...")
                
                if isinstance(data_to_write, (dict, list)):
                    print("  Konwersja słownika/listy do XML ElementTree przed zapisem...")
                    write_success = write_data_to_xml(data_to_write, parsed_args['output_path'])
                    if not write_success:
                        print("Program zakończył działanie z błędami podczas zapisu.")
                        exit(1)
                elif isinstance(data_to_write, ET.Element):
                    print("  Zapis obiektu ElementTree bezpośrednio do XML.")
                    write_success = write_data_to_xml(data_to_write, parsed_args['output_path'])
                    if not write_success:
                        print("Program zakończył działanie z błędami podczas zapisu.")
                        exit(1)
                else:
                    print(f"Ostrzeżenie: Nieobsługiwany typ danych dla zapisu do XML: {type(data_to_write)}. Pomięto zapis.")
                    exit(1) 

            else:
                print(f"Ostrzeżenie: Zapis do formatu '{parsed_args['output_format']}' nie jest jeszcze zaimplementowany.")

            print("Program zakończył działanie pomyślnie.") 
        else:
            print("Błąd walidacji pliku wejściowego. Program zostanie zakończony.")
            exit(1)


    except SystemExit as e:
        print(f"Błąd parsowania argumentów lub żądanie pomocy: {e}")
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}")