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

	print('==== Format Config %d ====' % (idx))
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

	config_len = print_specific_config_raw(read_bytes[40:])

	return 40 + config_len

'''
struct nhlt_fmt {
	u8 fmt_count;
	struct nhlt_fmt_cfg fmt_config[];
} __packed;
'''
def print_formats_config(read_bytes):
	fmt_count = read_bytes[0]
	start = 1

	print('==== Formats Config ====')
	print('count:\t\t\t%d' % (fmt_count))

	for idx in range(fmt_count):
		config_len = print_format_config(idx, read_bytes[start:])
		start += config_len

	#print('print_formats_config: len %d' % (start))
	return start

def print_specific_config_raw(read_bytes):
	size = struct.unpack('I', read_bytes[0:4])[0]

	print('==== Specific Config ====')
	print('size:\t\t\t%d' % (size))
	if size != 0:
		print('caps:\t\t\t%s' % (binascii.hexlify(read_bytes[4:4+size], b' ')))

	return 4 + size

'''
struct nhlt_specific_cfg {
	u32 size;
	u8 caps[];
} __packed;
'''
def print_specific_config(read_bytes):
	def get_array_type_string(array_type_ex):
		array_types = ['Linear 2-element, Small', 'Linear 2-element, Big', 'Linear 4-element, 1st geometry', 'Planar L-shaped 4-element', 'Linear 4-element, 2nd geometry', 'Vendor defined']
		extensions = ['No extension', 'Microphone SNR and Sensitivity extension', 'Reserved']

		array_type = array_type_ex & 0x0F

		if array_type < 0xA:
			return 'invalid'

		array_type -= 0xA

		if array_type >= len(array_types):
			return 'invalid'

		extension = (array_type_ex & 0xF0) >> 4

		if extension >= len(extensions):
			extension = len(extensions) - 1

		return array_types[array_type] + ' - ' + extensions[extension]

	config_len = print_specific_config_raw(read_bytes)

	if config_len == 4:
		return config_len

	print('virtual slot:\t\t%d' % (read_bytes[4]))

	config_type = read_bytes[5]
	if config_type == 0:
		print('config type:\t\t0 - Generic')
	elif config_type == 1:
		array_type_ex = read_bytes[6]
		print('config type:\t\t1 - Mic Array')
		print('array type:\t\t0x%x - %s' % (array_type_ex, get_array_type_string(array_type_ex)))
	elif config_type == 3:
		print('config type:\t3 - Render Feedback')
		print('feedback virtual slot:\t%d' % (read_bytes[6]))
		print('feedback channels:\t%d' % (struct.unpack('H', read_bytes[7:9])[0]))
		print('feedback valid bits per sample:\t%d' % (struct.unpack('H', read_bytes[9:11])[0]))
	else:
		print('config type:\t%d - not supported in Windows' % (config_type))

	#print('print_specific_config: len %d' % (config_len))
	return config_len

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

	specific_config_len = print_specific_config(read_bytes[19:])

	formats_config_len = print_formats_config(read_bytes[19+specific_config_len:])

	print('')

	#print('len %d' % (19+specific_config_len+formats_config_len))
	#print('print_endpoint_descriptor: len %d' % (length))
	return length

'''
struct acpi_table_header {
	char signature[ACPI_NAMESEG_SIZE];	/* ASCII table signature */
	u32 length;		/* Length of table in bytes, including this header */
	u8 revision;		/* ACPI Specification minor version number */
	u8 checksum;		/* To make sum of entire table == 0 */
	char oem_id[ACPI_OEM_ID_SIZE];	/* ASCII OEM identification */
	char oem_table_id[ACPI_OEM_TABLE_ID_SIZE];	/* ASCII OEM table identification */
	u32 oem_revision;	/* OEM revision number */
	char asl_compiler_id[ACPI_NAMESEG_SIZE];	/* ASCII ASL compiler vendor ID */
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
	print('oem revision:\t\t0x%x' % (struct.unpack('I', read_bytes[25:29])[0]))
	print('asl compiler id:\t%s' % (struct.unpack('4s', read_bytes[29:33])[0]))
	print('asl compiler revision:\t0x%x' % (struct.unpack('I', read_bytes[33:37])[0]))
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

	print('%d endpoint descriptors found\n' % (endpoint_count))

	for idx in range(endpoint_count):
		descriptor_len = print_endpoint_descriptor(idx, read_bytes[start:])
		start += descriptor_len

	if start < len(read_bytes):
		# OEDConfig exists
		config_len = print_specific_config_raw(read_bytes[start:])
		start += config_len

	#print('main: len %d' % (start))

	return

if __name__ == '__main__':
	main()
