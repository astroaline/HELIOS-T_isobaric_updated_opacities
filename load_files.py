import numpy as np
from input import *
import struct
import os


def load_opacity_data(molecule):
    ## Loads opacity tables from binary files ##

    #######################################################################################################

    # Filenames should be of the form Out_wavenumber minimum_wavenumber maximum_temperature_pressure.bin,
    # e.g. 'Out_1000_2000_1500_n300.bin' corresponds to an opacity file between 1000 and 2000 cm^-1 wavenumber,
    # at a temperature of 1500K and a pressure of 10^-3.00 bars.

    #######################################################################################################

    step_size = int(res/0.01)

    wavenumber_min = 1e4/wavelength_bins[-1]
    wavenumber_max = 1e4/wavelength_bins[0]

    index_min = int((wavenumber_min)/res)
    if 'log_xnh3' in parameters:   # ammonia only goes up to 12000 cm^-1
        x_full = np.r_[0:12000:res]
        index_max = len(x_full)
    else:
        x_full = np.r_[0:18000:res]
        index_max = int((wavenumber_max)/res) + 1

    pressure = int(np.log10(pressure_probed) * 100)
    if pressure < 0:
        pressure_str = 'n' + str(abs(pressure)).rjust(3, '0')   # pressure as in opacity filename
    else:
        pressure_str = 'p' + str(abs(pressure)).rjust(3, '0')

    temp = temp_dict[molecule]
    n_temp = len(temp)

    opacity_table = []
    for i in range(n_temp):
        temp_str = str(temp[i]).zfill(5)

        data = []

        wavenumber_dict = {'1H2-16O__POKAZATEL_e2b': '42000', '12C-1H4__YT10to10_e2b': '13000', '1H-12C-14N__Harris_e2b': '18000', '14N-1H3__CoYuTe_e2b': '20000'}

        filename = 'Out_00000_' + wavenumber_dict[molecule] + '_' + temp_str + '_' + pressure_str + '.bin'

        with open(opacity_path + molecule + '/' + filename, "rb") as f:
            byte = f.read(4)
            while byte:
                data.extend(struct.unpack("f", byte))
                byte = f.read(4)

        data = data[::step_size]
        opacity_table.append(data)

    opacity_table = np.array(opacity_table).T
    x_full = x_full[index_min:index_max]
    opacity_table = opacity_table[index_min:index_max, :]

    return x_full, opacity_table



def load_sigma(molecule1, molecule2, x_full):
    if os.path.exists(cia_path + molecule1 + '-' + molecule2 + '_2011.cia'):
        file_name = molecule1 + '-' + molecule2 + '_2011.cia'
    elif os.path.exists(cia_path + molecule1 + '-' + molecule2 + '_2018.cia'):
        file_name = molecule1 + '-' + molecule2 + '_2018.cia'
    elif os.path.exists(cia_path + molecule1 + '-' + molecule2 + '_2018b.cia'):
        file_name = molecule1 + '-' + molecule2 + '_2018b.cia'
    elif os.path.exists(cia_path + molecule1 + '-' + molecule2 + '_norm_2011.cia'):
        file_name = molecule1 + '-' + molecule2 + '_norm_2011.cia'
    elif os.path.exists(cia_path + molecule1 + '-' + molecule2 + '_eq_2011.cia'):
        file_name = molecule1 + '-' + molecule2 + '_eq_2011.cia'
    else:
        print('{}-{} not found'.format(molecule1,molecule2))
        import sys
        sys.exit(1)

    with open(cia_path + file_name) as file:
        data = file.readlines()

    header = str(data[0])
    header_list = header.split(' ')
    header_list = [x for x in header_list if x]

    lines_per_temp = float(header_list[3])

    num_temps = len(temperature_array_cia)

    cia_data = []
    wavenumber_array = np.r_[6250:10001:res]

    for i in range(int(num_temps)):
        j = int(i*(lines_per_temp+1))
        header = data[j]
        header_list = header.split(' ')
        header_list = [x for x in header_list if x]

        start_v = float(header_list[1])

        min_v = int(6251 - start_v)
        max_v = int(10002 - start_v)

        cia_line = []

        for k in range(min_v, max_v):           # For CIA, temperature goes down rows, wavenumber goes across columns
            data_line = data[j+k].split(' ')
            data_line = [x for x in data_line if x]
            cia_line.append(float(data_line[1][:-1]))

        cia_line = cia_line[::res]

        cia_data.append(cia_line)

    pad_start = int((x_full[0] - wavenumber_array[0]) / res)
    pad_end = int((x_full[-1] - wavenumber_array[-1]) / res)

    if pad_start > 0:
        cia_data = cia_data[:, pad_start:]
    else:
        cia_data = np.pad(cia_data, ((0, 0), (-pad_start, 0)), 'constant')

    if pad_end < 0:
        cia_data = cia_data[:, :pad_end]
    else:
        cia_data = np.pad(cia_data, ((0, 0), (0, pad_end)), 'constant')

    return cia_data
