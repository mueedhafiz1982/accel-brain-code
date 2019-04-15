# -*- coding: utf-8 -*-
import numpy as np
from pygan.true_sampler import TrueSampler


class BarTrueSampler(TrueSampler):
    '''
    Sampler which draws samples from the `true` distribution of MIDI files.
    '''

    def __init__(
        self, 
        midi_df_list, 
        batch_size=20, 
        seq_len=10, 
        time_fraction=0.1
    ):
        '''
        Init.

        Args:
            midi_df_list:      `list` of paths to MIDI data extracted by `MidiController`.
            batch_size:         Batch size.
            seq_len:            The length of sequneces.
                                The length corresponds to the number of `time` splited by `time_fraction`.

            time_fraction:      Time fraction which means the length of bars.
        '''
        program_list = []
        self.__midi_df_list = midi_df_list
        for i in range(len(self.__midi_df_list)):
            program_list.extend(
                self.__midi_df_list[i]["program"].drop_duplicates().values.tolist()
            )
        program_list = list(set(program_list))

        self.__batch_size = batch_size
        self.__seq_len = seq_len
        self.__channel = len(program_list)
        self.__program_list = program_list
        self.__time_fraction = time_fraction

    def draw(self):
        '''
        Draws samples from the `true` distribution.
        
        Returns:
            `np.ndarray` of samples.
        '''
        return np.concatenate((self.__create_samples(), self.__create_samples()), axis=1)

    def __create_samples(self):
        sampled_arr = np.zeros((self.__batch_size, self.__channel, self.__seq_len, 12))

        for batch in range(self.__batch_size):
            for i in range(len(self.__program_list)):
                program_key = self.__program_list[i]
                key = np.random.randint(low=0, high=len(self.__midi_df_list))
                midi_df = self.__midi_df_list[key]

                midi_df = midi_df[midi_df.program == program_key]
                if midi_df.shape[0] < self.__seq_len:
                    continue

                row = np.random.uniform(
                    low=midi_df.start.min(), 
                    high=midi_df.end.max() - (self.__seq_len * self.__time_fraction)
                )
                for seq in range(self.__seq_len):
                    df = midi_df[midi_df.start < row + (seq * self.__time_fraction)]
                    df = df[df.end > row + ((seq+1) * self.__time_fraction)]
                    sampled_arr[batch, i, seq] = self.__convert_into_feature(df)

        return sampled_arr

    def __convert_into_feature(self, df):
        arr = np.zeros(12)
        for i in range(df.shape[0]):
            arr[df.pitch.values[i] % 12] = 1

        return arr.reshape(1, -1).astype(float)
