import argparse
import os

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

if __name__ == "__main__":
    try:
        parsed_args = parse_arguments()
        print(f"Pomyślnie sparsowano argumenty:")
        print(f"  Plik wejściowy: {parsed_args['input_path']} (Format: {parsed_args['input_format']})")
        print(f"  Plik wyjściowy: {parsed_args['output_path']} (Format: {parsed_args['output_format']})")

    except SystemExit as e:
        print(f"Błąd parsowania argumentów lub żądanie pomocy: {e}")
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd: {e}")