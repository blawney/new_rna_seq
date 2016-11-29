import logging
import sys
import os
import json
import libcloud
from libcloud.storage.types import Provider
from libcloud.storage.drivers.google_storage import ObjectPermissions
import urllib2

sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import component_utils

class NoStorageProviderException(Exception):
	pass

def run(name, project):
	logging.info('Beginning cloud upload component of pipeline.')

	# get the location of the utils directory:
	utils_dir = project.parameters.get('utils_dir')

	# load the parser and the util_methods modules:
	util_methods = component_utils.load_remote_module('util_methods', utils_dir)

	# parse this module's config file
	this_dir = os.path.dirname(os.path.realpath(__file__))
	project.parameters.add(component_utils.parse_config_file(project, this_dir))
	component_params = component_utils.parse_config_file(project, this_dir, 'COMPONENT_SPECIFIC')
	
	# get the connection
	driver = get_connection_driver(project, component_params)
	logging.info('Created storage driver: %s' % driver)

	# get the root bucket:
	root_container = driver.get_container(component_params.get('storage_root'))

	# get the files to upload (and some metadate) in a dictionary.  These will populate
	# a descriptor JSON file which clients can use
	upload_contents = get_upload_content(project)
	logging.info('To upload:\n%s' % upload_contents)

	project_json_filepath = os.path.join(project.parameters.get('project_directory'), component_params.get('project_detail_file'))
	cccb_project_json = json.load(open(project_json_filepath))

	for x in upload_contents['files']:
		filepath = os.path.join(cccb_project_json.get('project_id'), x['name'])
		logging.info('About to upload %s to %s' % (x['path'], os.path.join(root_container.name, filepath)))
		driver.upload_object(x['path'], root_container, filepath)
		# for each of the permitted users, allow them to read
		for user in cccb_project_json.get('client_emails'):
			logging.info('Adding READ permission for client with email %s for object at %s' % (user, filepath))
			driver.ex_set_permissions(root_container.name, 
							object_name=urllib2.quote(filepath, safe=''), 
							entity="user-%s" % user, 
							role=ObjectPermissions.READER)
			

	# upload a JSON descriptor
	cccb_project_json.update(upload_contents)
	json_out = os.path.join(project.parameters.get('project_directory'), component_params.get('descriptor_file'))
	logging.info('Updated JSON descriptor located at %s' % json_out)
	with open(json_out, 'w') as fout:
		json.dump(cccb_project_json, fout)
	driver.upload_object(json_out, root_container, os.path.join(cccb_project_json.get('project_id'), component_params.get('descriptor_file')))
	
	return [None,]


def get_upload_content(project):

	# locate raw count files:
	# named like /<path>/raw_count_matrix.sort.primary.tsv
	all_raw_count_files = project.raw_count_matrices

	filepaths = [os.path.realpath(x) for x in all_raw_count_files]

	filenames = [os.path.basename(x) for x in all_raw_count_files]

	file_desc = ['.'.join(x.split('.')[:-1]) for x in filenames] # makes a comma-separated string like 'raw_count_matrix, sort, primary'

	filetypes = [x.split('.')[-1] for x in filenames] # e.g. 'tsv'
	
	j = {}
	j['files'] = []
	for i in range(len(filepaths)): 
		j['files'].append({
				'path': filepaths[i],
				'name': filenames[i],
				'type': filetypes[i],
				'desc': file_desc[i] })
	return j



def get_connection_driver(project, component_params):

	if component_params.get('storage_provider'): 
		# get the class for the proper driver
		cls = libcloud.storage.providers.get_driver(component_params.get('storage_provider'))
		logging.info('Storage provider: %s' % cls)
		credential_file =  os.path.join(os.path.dirname( os.path.abspath(__file__) ), component_params.get('credentials'))
		logging.info(credential_file)
		credentials_json = json.load( open(credential_file) )
		logging.info('credentials: %s' % credentials_json)
		# instantiate the class.
		# TODO: this call could be different depending on the provider and credential mechanism.  Perhaps make more generic?
		#driver = cls(key=credentials_json.get('client_email'), 
		driver = cls(key=credentials_json.get('client_id'), 
                     secret=credentials_json.get('secret'))
		logging.info('Created driver')
		driver.project_id = component_params.get('account')
		logging.info('Added project %s' % component_params.get('account'))
		return driver

	else:
		raise NoStorageProviderException('Fix issue with instantiating storage driver by checking params in the config file')








