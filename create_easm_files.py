import os
import random
import string


def create_easm_files(directory, num_files):
    if not os.path.exists(directory):
        os.makedirs(directory)

    for i in range(num_files):
        file_name = f"file_{i}.easm"
        file_path = os.path.join(directory, file_name)

        # Generate random content
        content = ''.join(random.choices(string.ascii_letters + string.digits, k=100))

        with open(file_path, 'w') as f:
            f.write(content)


if __name__ == "__main__":
    directory = './clientes/iaggo.capitanio@gmail.com/urn_ngsi-ld_project_chanut/Briefing/3D'
    N = 50
    create_easm_files(directory, N)
