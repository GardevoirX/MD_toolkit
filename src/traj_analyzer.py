from importlib_metadata import files
import mdtraj as md
import pickle
import argparse
import os
import random
import numpy as np
import pandas as pd
import MDAnalysis as mda

from src.io import read_file

class Traj():
    
    def __init__(self, topFile, trajName):
        
        self.traj = mda.Universe(trajName, topFile)
        self.features = pd.DataFrame()
        
    def add_features(self, featureName, feature):
        
        self.features[featureName] = feature

class TrajAnalyzer():

    def __init__(self, trajList, topFile) -> None:
        
        self.trajList = [os.path.abspath(file) for file in trajList]
        self.topFile = os.path.abspath(topFile)
        self.trajs = [Traj(trajFile, topFile) for trajFile in self.trajList]
        self.trajLens = [traj.traj.trajectory.n_frames for traj in self.trajs]
        
    def load_features(self, featureName, featureList):
        
        assert len(self.trajs) == len(featureList)
        for i, fileName in enumerate(featureList):
            feature = read_file(fileName)
            self.trajs[i].add_features(featureName, feature)
            
    def add_features(self, featureName, features):
        
        assert len(self.trajs) == len(features)
        for i, feature in enumerate(features):
            self.trajs[i].add_features(featureName, feature)
            
    def get_concatenated_features(self):
        
        return pd.concat(traj.features for traj in self.trajs)
    
    def sample_structures(self, pos:dict, selRange:dict, sampleNum=10):
        
        concatFeat = self.get_concatenated_features()
        for feature in pos:
            assert feature in concatFeat
        mask = np.full(len(concatFeat), True)
        for feature in pos:
            mask &= (np.abs(concatFeat[feature] - pos[feature]) < selRange[feature])
        masks = self._recover_concatenated_data(mask)
        
        selIndex = []
        for iTraj, mask in enumerate(masks):
            frameIndex = np.array(mask[mask].index.tolist())[np.newaxis, :].T
            trajIdxCol = np.full((len(frameIndex), 1), iTraj)
            selIndex.append(np.c_[trajIdxCol, frameIndex])
        selIndex = np.concatenate(selIndex)
        
        return selIndex[np.random.choice(len(selIndex), size=sampleNum)]
    
    def write_sampled_structures(self, selection, outputPref):
        
        outputPref = os.path.abspath(outputPref)
        if not os.path.exists(outputPref):
            os.makedirs(outputPref, exist_ok=True)
            
        for iTraj, iFrame in selection:
            outputFileName = os.path.join(outputPref, f'Traj-{iTraj}-{iFrame}.pdb')
            with mda.Writer(outputFileName) as writer:
                for ts in self.trajs[iTraj].traj.trajectory[iFrame:iFrame+1]:
                    writer.write(self.trajs[iTraj].traj)
            
    def _recover_concatenated_data(self, concatData):
        
        recoveredData = []
        l = 0
        r = 0
        for i in range(len(self.trajLens)):
            r += self.trajLens[i]
            recoveredData.append(concatData[l:r:])
            l += self.trajLens[i]
            
        return recoveredData
