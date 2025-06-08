import argparse
import os
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import yaml
import sys 

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QFileDialog, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Konwertuje dane z jednego formatu na inny (XML, JSON, YAML).",
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

    if not os.path.isabs(input_path):
        input_path = os.path.abspath(input_path)
    if not os.path.isabs(output_path):
        output_path = os.path.abspath(output_path)

    if not os.path.exists(input_path):
        parser.error(f"Błąd: Plik wejściowy '{input_path}' nie istnieje.")

    _, input_ext = os.path.splitext(input_path)
    _, output_ext = os.path.splitext(output_path)

    input_format = input_ext[1:].lower() if input_ext else None
    output_format = output_ext[1:].lower() if output_ext else None

    allowed_formats = ['xml', 'json', 'yml', 'yaml']

    if input_format not in allowed_formats:
        parser.error(f"Błąd: Nieobsługiwane rozszerzenie pliku wejściowego: '{input_ext}'. Oczekiwano: {', '.join(allowed_formats)}")
    if output_format not in allowed_formats:
        parser.error(f"Błąd: Nieobsługiwane rozszerzenie pliku wyjściowego: '{output_ext}'. Oczekiwano: {', '.join(allowed_formats)}")

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
                raise ValueError(f"Wewnętrzny błąd: Nieobsługiwany format dla wczytywania: {file_format}")
    except FileNotFoundError:
        print(f"Błąd krytyczny: Plik '{file_path}' nie został znaleziony podczas próby odczytu.")
        return None
    except json.JSONDecodeError as e:
        print(f"Błąd składni JSON w pliku '{file_path}': {e}")
        return None
    except ET.ParseError as e:
        print(f"Błąd składni XML w pliku '{file_path}': {e}")
        return None
    except yaml.YAMLError as e:
        print(f"Błąd składni YAML w pliku '{file_path}': {e}")
        return None
    except UnicodeDecodeError as e:
        print(f"Błąd kodowania znaków w pliku '{file_path}': {e}. Upewnij się, że plik jest w UTF-8.")
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
        print(f"Błąd zapisu do JSON: Dane nie mogą być serializowane. Upewnij się, że to słownik/lista: {e}")
        return False
    except IOError as e:
        print(f"Błąd zapisu do JSON: Problem z dostępem do pliku '{output_path}': {e}")
        return False
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd podczas zapisu do pliku JSON '{output_path}': {e}")
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
            item_tag = tag[:-1] if tag.endswith('s') and len(tag) > 1 else "item"
            if isinstance(item, dict):
                child_elem = ET.SubElement(elem, item_tag)
                for k, v in item.items():
                    if isinstance(v, (dict, list)):
                        sub_child = convert_dict_to_xml_element(k, v)
                        child_elem.append(sub_child)
                    else:
                        sub_child = ET.SubElement(child_elem, k)
                        sub_child.text = str(v)
            else:
                child_elem = ET.SubElement(elem, item_tag)
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
                raise TypeError(f"Błąd wewnętrzny: Nieobsługiwany typ danych do zapisu do XML: {type(data)}")

        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml_as_string = reparsed.toprettyxml(indent="  ")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml_as_string)
        print(f"  Pomyślnie zapisano dane do pliku XML: '{output_path}'.")
        return True
    except TypeError as e:
        print(f"Błąd zapisu do XML: Problem z typem danych lub konwersją: {e}")
        return False
    except IOError as e:
        print(f"Błąd zapisu do XML: Problem z dostępem do pliku '{output_path}': {e}")
        return False
    except ET.ParseError as e:
        print(f"Błąd XML parsowania podczas zapisu: {e}")
        return False
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd podczas zapisu do pliku XML '{output_path}': {e}")
        return False

def convert_xml_to_dict(element):
    result = {}

    if element.attrib:
        result.update(element.attrib)

    for child in element:
        child_data = convert_xml_to_dict(child)
        if child.tag in result:
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(child_data)
        else:
            result[child.tag] = child_data

    if element.text and element.text.strip():
        text_content = element.text.strip()
        if not result and not element.attrib:
            return text_content
        elif text_content:
            result['#text'] = text_content

    return result

def write_data_to_yaml(data, output_path):
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"  Pomyślnie zapisano dane do pliku YAML: '{output_path}'.")
        return True
    except TypeError as e:
        print(f"Błąd zapisu do YAML: Dane nie mogą być serializowane. Upewnij się, że to słownik/lista: {e}")
        return False
    except IOError as e:
        print(f"Błąd zapisu do YAML: Problem z dostępem do pliku '{output_path}': {e}")
        return False
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd podczas zapisu do pliku YAML '{output_path}': {e}")
        return False

class ConverterWorker(QThread):
    finished = pyqtSignal(bool, str) 
    progress = pyqtSignal(str) 

    def __init__(self, input_path, input_format, output_path, output_format):
        super().__init__()
        self.input_path = input_path
        self.input_format = input_format
        self.output_path = output_path
        self.output_format = output_format

    def run(self):
        try:
            self.progress.emit("Rozpoczynanie konwersji w tle...")

            input_data = read_and_validate_data(
                self.input_path,
                self.input_format
            )

            if input_data is None:
                self.finished.emit(False, "Nie udało się wczytać lub zweryfikować pliku wejściowego. Sprawdź logi.")
                return

            self.progress.emit("Walidacja pliku wejściowego zakończona sukcesem.")

            data_for_conversion = None
            if self.input_format == 'xml':
                if isinstance(input_data, ET.Element):
                    self.progress.emit("  Konwersja XML (ElementTree) na słownik/listę Pythona...")
                    data_for_conversion = convert_xml_to_dict(input_data)
                    if data_for_conversion is None:
                        self.finished.emit(False, "Konwersja XML na wewnętrzny format nie powiodła się.")
                        return
                else:
                    self.finished.emit(False, f"Błąd wewnętrzny: Oczekiwano obiektu ElementTree dla formatu XML, otrzymano {type(input_data)}.")
                    return
            elif self.input_format in ['json', 'yaml']:
                data_for_conversion = input_data
                self.progress.emit(f"  Dane wejściowe są już w formie słownika/listy Pythona (z {self.input_format.upper()}).")
            else:
                self.finished.emit(False, f"Błąd wewnętrzny: Nieznany format wejściowy do konwersji: {self.input_format}.")
                return

            write_success = False
            if self.output_format == 'json':
                self.progress.emit("\nRozpoczynanie zapisu danych do pliku JSON...")
                write_success = write_data_to_json(data_for_conversion, self.output_path)
            elif self.output_format == 'xml':
                self.progress.emit("\nRozpoczynanie zapisu danych do pliku XML...")
                write_success = write_data_to_xml(data_for_conversion, self.output_path)
            elif self.output_format == 'yaml':
                self.progress.emit("\nRozpoczynanie zapisu danych do pliku YAML...")
                write_success = write_data_to_yaml(data_for_conversion, self.output_path)
            else:
                self.finished.emit(False, f"Błąd wewnętrzny: Nieznany format wyjściowy do zapisu: {self.output_format}.")
                return

            if write_success:
                self.finished.emit(True, "Konwersja zakończona pomyślnie!")
            else:
                self.finished.emit(False, "Wystąpił błąd podczas konwersji. Sprawdź logi.")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.progress.emit(f"FATALNY BŁĄD WĄTKU KONWERSJI: {e}\n{error_details}")
            self.finished.emit(False, f"Wystąpił nieoczekiwany błąd globalny: {e}")

class DataConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Konwerter Danych (XML, JSON, YAML)')
        self.setGeometry(100, 100, 700, 450)

        main_layout = QVBoxLayout()

        input_layout = QHBoxLayout()
        self.input_label = QLabel('Plik wejściowy:')
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("Wybierz plik wejściowy...")
        self.input_browse_btn = QPushButton('Przeglądaj...')
        self.input_browse_btn.clicked.connect(self.browse_input_file)
        self.input_format_label = QLabel('Format wejściowy:')
        self.input_format_combo = QComboBox()
        self.input_format_combo.addItems(['json', 'xml', 'yaml'])

        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_path_edit)
        input_layout.addWidget(self.input_browse_btn)
        input_layout.addWidget(self.input_format_label)
        input_layout.addWidget(self.input_format_combo)
        main_layout.addLayout(input_layout)

        output_layout = QHBoxLayout()
        self.output_label = QLabel('Plik wyjściowy:')
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Wybierz lub wprowadź nazwę pliku wyjściowego...")
        self.output_browse_btn = QPushButton('Przeglądaj...')
        self.output_browse_btn.clicked.connect(self.browse_output_file)
        self.output_format_label = QLabel('Format wyjściowy:')
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(['json', 'xml', 'yaml'])

        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(self.output_browse_btn)
        output_layout.addWidget(self.output_format_label)
        output_layout.addWidget(self.output_format_combo)
        main_layout.addLayout(output_layout)

        self.convert_btn = QPushButton('Konwertuj')
        self.convert_btn.setFixedHeight(40)
        self.convert_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.convert_btn.clicked.connect(self.perform_conversion)
        main_layout.addWidget(self.convert_btn)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        main_layout.addWidget(QLabel("Logi operacji:"))
        main_layout.addWidget(self.log_output)

        self.setLayout(main_layout)

        self.input_path_edit.textChanged.connect(self.update_input_format)

        self.output_path_edit.textChanged.connect(self.update_output_format)

    def update_input_format(self):
        file_path = self.input_path_edit.text()
        _, ext = os.path.splitext(file_path)
        ext = ext[1:].lower()
        if ext == 'yml':
            ext = 'yaml'

        index = self.input_format_combo.findText(ext)
        if index >= 0:
            self.input_format_combo.setCurrentIndex(index)

    def update_output_format(self):
        file_path = self.output_path_edit.text()
        _, ext = os.path.splitext(file_path)
        ext = ext[1:].lower()
        if ext == 'yml':
            ext = 'yaml'

        index = self.output_format_combo.findText(ext)
        if index >= 0:
            self.output_format_combo.setCurrentIndex(index)

    def browse_input_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Wybierz plik wejściowy", "", "Wszystkie pliki (*);;JSON pliki (*.json);;XML pliki (*.xml);;YAML pliki (*.yaml *.yml)")
        if file_name:
            self.input_path_edit.setText(file_name)

    def browse_output_file(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Zapisz plik wyjściowy jako", "", "Wszystkie pliki (*);;JSON pliki (*.json);;XML pliki (*.xml);;YAML pliki (*.yaml *.yml)")
        if file_name:
            self.output_path_edit.setText(file_name)

    def log_message(self, message):
        self.log_output.append(message)
        QApplication.processEvents() 

    def perform_conversion(self):
        self.log_output.clear()
        self.log_message("Rozpoczynanie konwersji...")

        input_path = self.input_path_edit.text()
        output_path = self.output_path_edit.text()
        input_format = self.input_format_combo.currentText()
        output_format = self.output_format_combo.currentText()

        if not input_path or not output_path:
            QMessageBox.warning(self, "Błąd", "Proszę podać ścieżki do obu plików (wejściowego i wyjściowego).")
            self.log_message("Błąd: Nie podano wszystkich ścieżek.")
            return

        if not os.path.exists(input_path):
            QMessageBox.warning(self, "Błąd", f"Plik wejściowy '{input_path}' nie istnieje.")
            self.log_message(f"Błąd: Plik wejściowy '{input_path}' nie istnieje.")
            return

        self.log_message(f"  Plik wejściowy: {input_path} (Format: {input_format})")
        self.log_message(f"  Plik wyjściowy: {output_path} (Format: {output_format})")

    
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("Konwertuję...")

        self.worker = ConverterWorker(input_path, input_format, output_path, output_format)
        self.worker.finished.connect(self.on_conversion_finished)
        self.worker.progress.connect(self.log_message) 
        self.worker.start() 

    def on_conversion_finished(self, success, message):
        self.convert_btn.setEnabled(True) 
        self.convert_btn.setText("Konwertuj")

        self.log_message(message)
        if success:
            QMessageBox.information(self, "Sukces", message)
        else:
            QMessageBox.critical(self, "Błąd Konwersji", message)
      
if __name__ == '__main__':
    if len(sys.argv) > 1:
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

            if input_data is None:
                print("Błąd: Nie udało się wczytać lub zweryfikować pliku wejściowego. Program zostanie zakończony.")
                sys.exit(1)

            data_for_conversion = None
            if parsed_args['input_format'] == 'xml':
                if isinstance(input_data, ET.Element):
                    print("  Konwersja XML (ElementTree) na słownik/listę Pythona...")
                    data_for_conversion = convert_xml_to_dict(input_data)
                    if data_for_conversion is None:
                        print("Błąd: Konwersja XML na słownik Pythona nie powiodła się.")
                        sys.exit(1)
                else:
                    print(f"Błąd wewnętrzny: Oczekiwano obiektu ElementTree dla formatu XML, otrzymano {type(input_data)}.")
                    sys.exit(1)
            elif parsed_args['input_format'] in ['json', 'yaml']:
                data_for_conversion = input_data
                print(f"  Dane wejściowe są już w formie słownika/listy Pythona (z {parsed_args['input_format'].upper()}).")
            else:
                print(f"Błąd wewnętrzny: Nieznany format wejściowy do konwersji: {parsed_args['input_format']}.")
                sys.exit(1)

            write_success = False
            if parsed_args['output_format'] == 'json':
                print("\nRozpoczynanie zapisu danych do pliku JSON...")
                write_success = write_data_to_json(data_for_conversion, parsed_args['output_path'])
            elif parsed_args['output_format'] == 'xml':
                print("\nRozpoczynanie zapisu danych do pliku XML...")
                write_success = write_data_to_xml(data_for_conversion, parsed_args['output_path'])
            elif parsed_args['output_format'] == 'yaml':
                print("\nRozpoczynanie zapisu danych do pliku YAML...")
                write_success = write_data_to_yaml(data_for_conversion, parsed_args['output_path'])
            else:
                print(f"Błąd wewnętrzny: Nieznany format wyjściowy do zapisu: {parsed_args['output_format']}.")
                sys.exit(1)

            if write_success:
                print("\nProgram zakończył działanie pomyślnie.")
                sys.exit(0)
            else:
                print("\nProgram zakończył działanie z błędami podczas zapisu.")
                sys.exit(1)

        except SystemExit as e:
            if e.code == 0:
                print("Program zakończył działanie (np. wyświetlono pomoc).")
            else:
                print(f"Program zakończył działanie z kodem błędu: {e.code}.")
            sys.exit(e.code)
        except Exception as e:
            print(f"\nFATALNY BŁĄD: Wystąpił nieoczekiwany błąd globalny: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else: 
        app = QApplication(sys.argv)
        window = DataConverterApp()
        window.show()
        sys.exit(app.exec())