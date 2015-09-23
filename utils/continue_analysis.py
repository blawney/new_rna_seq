import util_methods
import logging
import itertools

class MissingContrastsException(Exception):
	pass

class MissingAnnotationException(Exception):
	pass


def configure_for_restart(configured_pipeline, annotation_filepath = None, contrast_filepath = None):
                       
	# !! Change the skip_analysis flag to False so the DGE components are run !!
	configured_pipeline.project.parameters.reset_param('skip_analysis', False)
	
	if not configured_pipeline.project.contrasts:
		if not annotation_filepath:
			raise MissingContrastsException('The initial run did not specify contrasts, and you did not supply a commandline path to a sample annotation file.  Please fix that and try again.')
		else:
			pairing_list = util_methods.parse_annotation_file(annotation_filepath)
			logging.info('Read the following pairing list from the annotation file: %s' % pairing_list)
			
			# do a quick sanity check on the samples provided:
			supplied_sample_names = [x[0] for x in pairing_list]
			previous_sample_names_accounted = all([s.sample_name in supplied_sample_names for s in configured_pipeline.project.samples])

			# if the annotation file had at least all the samples that were initially considered
			if previous_sample_names_accounted:
				logging.info('All the samples used in the initial alignment are in the annotation file.  Getting conditions and contrasts now.')
				sample_to_condition_map = dict(pairing_list)
				conditions = set()
				for s in configured_pipeline.project.samples:
					c = sample_to_condition_map[s.sample_name]
					s.condition = c
					conditions.add(c)

				if contrast_filepath:
					contrast_pairings = util_methods.parse_annotation_file(contrast_filepath)
					logging.info('Contrast pairings from contrast file: %s' % contrast_pairings)
					conditions_from_file = set(reduce(lambda x,y: list(x)+list(y), contrast_pairings))
					logging.info('Conditions represented in contrast file: %s ' % conditions_from_file)
					if len(conditions_from_file.difference(conditions)) > 0:
						raise UnrepresentedGroupException('You specified a group in the contrast file that has no samples.')
				else:
					contrast_pairings = set(itertools.combinations(conditions, 2))
				configured_pipeline.project.contrasts = contrast_pairings

			else:
				logging.error('Not all of the samples were found in the annotation file.  All samples: %s' % configured_pipeline.project.samples)
				raise MissingAnnotationException('Missing samples in annotation file.  Check over the log messages to see which may have been missed.')
