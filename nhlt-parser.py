#!/usr/bin/env python3
import binascii
import struct
import uuid

HNLT_FILE = "/sys/firmware/acpi/tables/NHLT"

'''
struct wav_fmt {
	u16 fmt_tag;
	u16 channels;
	u32 samples_per_sec;
	u32 avg_bytes_per_sec;
	u16 block_align;
	u16 bits_per_sample;
	u16 cb_size;
} __packed;

struct wav_fmt_ext {
	struct wav_fmt fmt;
	union samples {
		u16 valid_bits_per_sample;
		u16 samples_per_block;
		u16 reserved;
	} sample;
	u32 channel_mask;
	u8 sub_fmt[16];
} __packed;

struct nhlt_fmt_cfg {
	struct wav_fmt_ext fmt_ext;
	struct nhlt_specific_cfg config;
} __packed;
'''
def print_format_config(idx, read_bytes):
	def get_channel_mask_string(channel_mask):
		channel_masks = ['SPEAKER_FRONT_LEFT', 'SPEAKER_FRONT_RIGHT', 'SPEAKER_FRONT_CENTER', 'SPEAKER_LOW_FREQUENCY', 'SPEAKER_BACK_LEFT', 'SPEAKER_BACK_RIGHT', 'SPEAKER_FRONT_LEFT_OF_CENTER', 'SPEAKER_FRONT_RIGHT_OF_CENTER', 'SPEAKER_BACK_CENTER', 'SPEAKER_SIDE_LEFT', 'SPEAKER_SIDE_RIGHT', 'SPEAKER_TOP_CENTER', 'SPEAKER_TOP_FRONT_LEFT', 'SPEAKER_TOP_FRONT_CENTER', 'SPEAKER_TOP_FRONT_RIGHT', 'SPEAKER_TOP_BACK_LEFT', 'SPEAKER_TOP_BACK_CENTER', 'SPEAKER_TOP_BACK_RIGHT'
]
		mask = 0x1
		mask_string = ''

		for idx in range(len(channel_masks)):
			if mask & channel_mask:
				if len(mask_string):
					mask_string += ' '
				mask_string += channel_masks[idx]
			mask <<= 1

		if len(mask_string) == 0:
			mask_string = 'NONE'

		return mask_string

	channel_mask = struct.unpack('I', read_bytes[20:24])[0]

	print('==== Format %d ====' % (idx))
	print('format tag:\t\t0x%x' % (struct.unpack('H', read_bytes[0:2])[0]))
	print('channels:\t\t%d' % (struct.unpack('H', read_bytes[2:4])[0]))
	print('samples per sec:\t%d' % (struct.unpack('I', read_bytes[4:8])[0]))
	print('avg bytes per sec:\t%d' % (struct.unpack('I', read_bytes[8:12])[0]))
	print('block align:\t\t%d' % (struct.unpack('H', read_bytes[12:14])[0]))
	print('bits per sample:\t%d' % (struct.unpack('H', read_bytes[14:16])[0]))
	print('cb size:\t\t%d' % (struct.unpack('H', read_bytes[16:18])[0]))
	print('valid bits per sample:\t%d' % (struct.unpack('H', read_bytes[18:20])[0]))
	print('channel mask:\t\t0x%x - %s' % (channel_mask, get_channel_mask_string(channel_mask)))
	print('subformat:\t\t%s' % (str(uuid.UUID(bytes = read_bytes[24:40]))))

	config_len = print_specific_config('Format %d Config' % (idx), read_bytes[40:])

	return 40 + config_len

'''
struct nhlt_fmt {
	u8 fmt_count;
	struct nhlt_fmt_cfg fmt_config[];
} __packed;
'''
def print_formats_config(read_bytes):
	format_count = read_bytes[0]
	start = 1

	print('==== Format Configs ====')
	print('count:\t\t\t%d' % (format_count))

	for idx in range(format_count):
		config_len = print_format_config(idx, read_bytes[start:])
		start += config_len

	return start

def print_vendor_mic_config(idx, read_bytes):
	def get_mic_type_string(mic_type):
		mic_types = ['KSMICARRAY_MICTYPE_OMNIDIRECTIONAL', 'KSMICARRAY_MICTYPE_SUBCARDIOID', 'KSMICARRAY_MICTYPE_CARDIOID', 'KSMICARRAY_MICTYPE_SUPERCARDIOID', 'KSMICARRAY_MICTYPE_HYPERCARDIOID', 'KSMICARRAY_MICTYPE_8SHAPED', 'Reserved', 'KSMICARRAY_MICTYPE_VENDORDEFINED']

		if mic_type >= len(mic_types):
			return 'invalid'

		return mic_types[mic_type]

	def get_panel_location_string(panel_location):
		panel_locations = ['Top', 'Bottom', 'Left', 'Right', 'Front (default)', 'Rear']

		if panel_location >= len(panel_locations):
			return 'invalid'

		return panel_locations[panel_location]

	mic_type = read_bytes[0]
	panel_location = read_bytes[1]

	print('==== Vendor Microphone Config %d ====' % (idx))
	print('type:\t\t\t%d - %s' % (mic_type, get_mic_type_string(mic_type)))
	print('panel:\t\t\t%d - %s' % (panel_location, get_panel_location_string(panel_location)))
	print('distance:\t\t%d' % (struct.unpack('h', read_bytes[2:4])[0]))
	print('horizontal offset:\t%d' % (struct.unpack('h', read_bytes[4:6])[0]))
	print('vertical offset:\t%d' % (struct.unpack('h', read_bytes[6:8])[0]))
	print('frequency low band:\t%d' % (read_bytes[8]))
	print('frequency high band:\t%d' % (read_bytes[9]))
	print('direction angle:\t%d' % (struct.unpack('h', read_bytes[10:12])[0]))
	print('elevation angle:\t%d' % (struct.unpack('h', read_bytes[12:14])[0]))
	print('work v angle begin:\t%d' % (struct.unpack('h', read_bytes[14:16])[0]))
	print('work v angle end:\t%d' % (struct.unpack('h', read_bytes[16:18])[0]))
	print('work h angle begin:\t%d' % (struct.unpack('h', read_bytes[18:20])[0]))
	print('work h angle end:\t%d' % (struct.unpack('h', read_bytes[20:22])[0]))

	return 22

'''
struct nhlt_specific_cfg {
	u32 size;
	u8 caps[];
} __packed;
'''
def print_specific_config(title, read_bytes):
	size = struct.unpack('I', read_bytes[0:4])[0]

	print('==== %s ====' % (title))
	print('size:\t\t\t%d' % (size))
	if size != 0:
		print('caps:\t\t\t%s' % (binascii.hexlify(read_bytes[4:4+size], b' ')))

	return 4 + size

'''
struct nhlt_device_specific_config {
	u8 virtual_slot;
	u8 config_type;
} __packed;
'''
def print_device_specific_config(read_bytes, config_len):
	def get_config_type_string(config_type):
		config_types = ['Generic', 'Mic Array', 'Render with Loopback', 'Render Feedback']

		if config_type >= len(config_types):
			return 'invalid'

		return config_types[config_type]

	def get_array_type_string(array_type, extension):
		array_types = ['Linear 2-element, Small', 'Linear 2-element, Big', 'Linear 4-element, 1st geometry', 'Planar L-shaped 4-element', 'Linear 4-element, 2nd geometry', 'Vendor defined']
		extensions = ['No extension', 'Microphone SNR and Sensitivity extension', 'Reserved']

		if array_type < 0xA:
			return 'invalid'

		array_type -= 0xA

		if array_type >= len(array_types):
			return 'invalid'

		if extension >= len(extensions):
			extension = len(extensions) - 1

		return array_types[array_type] + ' - ' + extensions[extension]

	config_type = read_bytes[1]
	start = 2

	print('virtual slot:\t\t%d' % (read_bytes[0]))
	print('config type:\t\t%d - %s' % (config_type, get_config_type_string(config_type)))

	if config_type == 1:
		# mic array
		array_type_ex = read_bytes[2]
		start += 1

		array_type = array_type_ex & 0x0F
		extension = (array_type_ex & 0xF0) >> 4

		print('array type:\t\t0x%x - %s' % (array_type_ex, get_array_type_string(array_type, extension)))

		if array_type == 0xF:
			# vendor defined
			mic_count = read_bytes[start]
			start += 1

			print('number of microphones:\t%d' % (mic_count))

			for idx in range(mic_count):
				mic_config_len = print_vendor_mic_config(idx, read_bytes[start:])
				start += mic_config_len

		if extension == 1:
			# snr and sensitivity extension
			# TODO: need to test with real device
			snr = struct.unpack('I', read_bytes[start:start+4])[0]
			sensitivity = struct.unpack('I', read_bytes[start+4:start+8])[0]
			start += 8

			print('snr:\t%d.%d' % (snr >> 16, snr & 0xFFFF))
			print('sensitivity:\t%d.%d' % (sensitivity >> 16, sensitivity & 0xFFFF))

	elif config_type == 3:
		# render feedback
		print('feedback virtual slot:\t%d' % (read_bytes[2]))
		print('feedback channels:\t%d' % (struct.unpack('H', read_bytes[3:5])[0]))
		print('feedback valid bits per sample:\t%d' % (struct.unpack('H', read_bytes[5:7])[0]))

		start = 7

	if config_len != start:
		print('device specific config: length %d, parsed %d' % (config_len, start))

'''
struct nhlt_endpoint {
	u32  length;
	u8   linktype;
	u8   instance_id;
	u16  vendor_id;
	u16  device_id;
	u16  revision_id;
	u32  subsystem_id;
	u8   device_type;
	u8   direction;
	u8   virtual_bus_id;
	struct nhlt_specific_cfg config;
} __packed;
'''
def print_endpoint_descriptor(idx, read_bytes):
	def get_link_type_string(link_type):
		link_types = ['HD-Audio', 'DSP', 'PDM', 'SSP', 'Slimbus', 'SoundWire', 'Reserved', 'Reserved']

		if link_type >= len(link_types):
			return 'invalid'

		return link_types[link_type]

	def get_device_type_string(link_type, device_type):
		ssp_device_types = ['BT Sideband', 'FM', 'Modem', 'Reserved', 'SSP Analog Codec', 'Reserved', 'Reserved', 'Reserved']

		if link_type == 2: # PDM
			if device_type > 0:
				return 'Reserved'
			else:
				return 'PDM'
		elif link_type == 3: # SSP
			if device_type >= len(ssp_device_types):
				return 'invalid'

			return ssp_device_types[device_type]

		return 'invalid'

	def get_direction_string(direction):
		directions = ['Render', 'Capture']

		if direction >= len(directions):
			return 'invalid'

		return directions[direction]

	length = struct.unpack('I', read_bytes[0:4])[0]
	link_type = read_bytes[4]
	device_type = read_bytes[16]
	direction = read_bytes[17]

	print('==== Endpoint Descriptor %d ====' % (idx))
	print('length:\t\t\t%d' % (length))
	print('link type:\t\t%d - %s' % (link_type, get_link_type_string(link_type)))
	print('instance id:\t\t%d' % (read_bytes[5]))
	print('vendor id:\t\t0x%x' % (struct.unpack('H', read_bytes[6:8])[0]))
	print('device id:\t\t0x%x' % (struct.unpack('H', read_bytes[8:10])[0]))
	print('revision id:\t\t%d' % (struct.unpack('H', read_bytes[10:12])[0]))
	print('subsystem id:\t\t%d' % (struct.unpack('I', read_bytes[12:16])[0]))
	print('device type:\t\t%d - %s' % (device_type, get_device_type_string(link_type, device_type)))
	print('direction:\t\t%d - %s' % (direction, get_direction_string(direction)))
	print('virtual bus id:\t\t%d' % (read_bytes[18]))

	start = 19
	config_len = print_specific_config('Endpoint Config', read_bytes[start:])

	if config_len > 4:
		print_device_specific_config(read_bytes[start+4:], config_len-4)
	else:
		print('endpoint_descriptor: missing endpoint config')

	start += config_len

	config_len = print_formats_config(read_bytes[start:])
	start += config_len

	print('')

	if start != length:
		print('endpoint_descriptor: length %d, parsed %d' % (length, start))

	return length

'''
struct acpi_table_header {
	char signature[4];	/* ASCII table signature */
	u32 length;		/* Length of table in bytes, including this header */
	u8 revision;		/* ACPI Specification minor version number */
	u8 checksum;		/* To make sum of entire table == 0 */
	char oem_id[6];	/* ASCII OEM identification */
	char oem_table_id[8];	/* ASCII OEM table identification */
	u32 oem_revision;	/* OEM revision number */
	char asl_compiler_id[4];	/* ASCII ASL compiler vendor ID */
	u32 asl_compiler_revision;	/* ASL compiler version */
};
'''
def print_acpi_header(read_bytes):
	print('==== ACPI Header ====')
	print('signature:\t\t%s' % (struct.unpack('4s', read_bytes[0:4])[0]))
	print('length:\t\t\t%d' % struct.unpack('I', read_bytes[4:8])[0])
	print('revision:\t\t%d' % (read_bytes[8]))
	print('checksum:\t\t%d' % (read_bytes[9]))
	print('oem id:\t\t\t%s' % (struct.unpack('6s', read_bytes[10:16])[0]))
	print('oem table id:\t\t%s' % (struct.unpack('8s', read_bytes[16:24])[0]))
	print('oem revision:\t\t0x%x' % (struct.unpack('I', read_bytes[24:28])[0]))
	print('creator id:\t\t%s' % (struct.unpack('4s', read_bytes[28:32])[0]))
	print('creator revision:\t0x%x' % (struct.unpack('I', read_bytes[32:36])[0]))
	print('')

	return 36

def main():
	with open(HNLT_FILE, 'rb') as file:
		read_bytes = file.read()

	start = 0
	header_len = print_acpi_header(read_bytes[start:])
	start += header_len

	endpoint_count = read_bytes[start]
	start += 1

	print('main: %d endpoint descriptors found\n' % (endpoint_count))

	for idx in range(endpoint_count):
		descriptor_len = print_endpoint_descriptor(idx, read_bytes[start:])
		start += descriptor_len

	if start < len(read_bytes):
		# OEDConfig exists
		config_len = print_specific_config('OED Config', read_bytes[start:])
		start += config_len
	else:
		print('main: missing OED config')

	if start != len(read_bytes):
		print('main: length %d, %d parsed' % (read_bytes, start))

	return

if __name__ == '__main__':
	main()
