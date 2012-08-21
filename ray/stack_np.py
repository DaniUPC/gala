# built-ins
import libNeuroProofRag as neuroproof
import morpho
import json

from numpy import zeros_like, array, double, zeros
import numpy

def get_prob_handle(classifier):
    def get_prob(features):
        prediction = classifier.predict_proba(array(features))[0,1]
        return float(prediction)
    return get_prob

class Stack:
    """Region adjacency graph for segmentation of nD volumes."""

    def __init__(self, watershed=numpy.array([]), probabilities=numpy.array([]),
                single_channel=True, classifier=None, synapse_file=None, feature_info=None,
                master_logger=None): 
        """Create a graph from a watershed volume and image volume.
        
        """

        self.depth, self.height, self.width = watershed.shape
        self.master_logger = master_logger


        self.watershed = morpho.pad(watershed, 0)
        self.watershed = self.watershed.astype(numpy.double)    

        probs = probabilities.astype(numpy.double)

        self.stack = neuroproof.build_stack(self.watershed)

        self.fmgr = self.stack.get_feature_mgr()
        num_channels = 1

        if single_channel:
            self.probabilities = morpho.pad(probs, 0)
            neuroproof.add_prediction_channel(self.stack, self.probabilities)
        else:
            num_channels = probabilities.shape[probabilities.ndim-1]
            for channel in range(0,num_channels):
                curr_prob = morpho.pad(probs[...,channel], 0)
                neuroproof.add_prediction_channel(self.stack, curr_prob)
                

        if classifier is not None:
            self.fmgr.set_python_rf_function(get_prob_handle(classifier))
                    
            if feature_info is not None:
                for feature in feature_info['feature_list']:
                    desc = feature_info[feature]
                    if feature == "histogram":
                        self.fmgr.add_hist_feature(desc["nbins"], desc["compute_percentiles"], False) 
                    elif feature == "moments":
                        self.fmgr.add_moment_feature(desc["nmoments"], desc["use_diff"]) 
                    else:
                        raise Exception("Feature " + feature + " not supported in NeuroProof") 
            else:
                raise Exception("No feature information for Rag")
            
        self.stack.build_rag()

        if synapse_file is not None:
            self.set_exclusions(synapse_file)

    def number_of_nodes(self):
        return self.stack.get_num_bodies()

    def __copy__(self):
        raise Exception("Not implemented yet")

    def copy(self):
        raise Exception("Not implemented yet")

    def agglomerate(self, threshold=0.5):
        self.stack.agglomerate_rag(threshold) 

    # already complete when the internal values are set to watershed and 1 
    def get_segmentation(self):
        seg_buffer = numpy.zeros((self.depth, self.height, self.width), numpy.uint32)
        neuroproof.write_volume_to_buffer(self.stack, seg_buffer)
        return seg_buffer

    def remove_inclusions(self):
        self.stack.remove_inclusions()    

    # just a simple rag export -- need feature for max size in a specified dimension
    def write_plaza_json(self, fout, synapse_file):
        print "Should be writing plaza json but not because I am a jerk"
        #raise Exception("Not implemented yet")

    def set_exclusions(self, synapse_volume):
        syn_file = open(synapse_volume, 'r')
        json_vals = json.load(syn_file)

        self.all_syn_locs = [] 

        for item in json_vals["data"]:
            curr_locs = []
            loc_arr = (item["T-bar"])["location"]
            loc = (loc_arr[0], loc_arr[1], loc_arr[2])
            
            self.all_syn_locs.append(loc)
            curr_locs.append(loc)

            for psd in item["partners"]:
                loc_arr = psd["location"]
                loc = (loc_arr[0], loc_arr[1], loc_arr[2])
                
                self.all_syn_locs.append(loc)
                curr_locs.append(loc)

            for i in range(0, len(curr_locs)):
                for j in range(i+1, len(curr_locs)):
                    status = self.stack.add_edge_constraint(curr_locs[i], curr_locs[j]) 
                    if not status and self.master_logger is not None:
                        self.master_logger.error("Tbar/PSD lie in same superpixel")     


    def learn_agglomerate(self, gts, feature_map, min_num_samples=1,
                                *args, **kwargs):
        raise Exception("Learn agglomerate not implemented in NeuroProof yet")



