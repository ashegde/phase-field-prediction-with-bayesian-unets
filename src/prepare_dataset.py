"""
Dataset Preparation

This module generates training, validation, and test datasets.
These datasets are constructed using the imported Cahn-Hilliard simulator,
and are saved in the HDF5 format.
"""
import argparse
import os
import pickle

import h5py
import numpy as np
from tqdm import tqdm

from simulator.simulator import CahnHilliardSimulator

def main(args: argparse.Namespace) -> None:
    # Create a directory for storing data if it does not exist
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Set a random seed for reproducibility
    seed_val = 2023
    np.random.seed(seed_val)

    # Define the number of experiments for each mode
    experiments = {
        'train': args.n_train,
        'valid': args.n_valid,
        'test': args.n_test,
    }

    experiment_durations = {
        'train': args.n_steps_train,
        'valid': args.n_steps_train,
        'test': args.n_steps_test,
    }

    # Initialize and save the Cahn-Hilliard simulator
    simulator = CahnHilliardSimulator(dt=args.dt)
    with open(f'{data_dir}/simulator.pkl', 'wb') as f:
        pickle.dump(simulator, f)

    # Generate datasets for each mode (train, valid, test)
    for mode, n_experiments in experiments.items():
        # Define file name for the current mode's dataset
        file_name = os.path.join(data_dir, f'{mode}_data.h5')

        # Create an HDF5 file to store the simulation data
        with h5py.File(file_name, 'w') as h5f:
            for ii in tqdm(range(n_experiments), desc=f'{mode}'):
                
                # Work in progress -- initialization of concentration field.
                # The choice of nominal concentration and noise strongly impacts
                # the geometry of the phase field during its evolution. In an ML context,  
                # this directly impacts the diversity of the training data.

                u0_nominal = (2.0*np.random.rand()-1.0) * np.ones((simulator.x_res, simulator.y_res))
                u0_noise = args.init_noise_scale * (2.0*np.random.rand(simulator.x_res, simulator.y_res)-1.0)
                u_init = np.clip(u0_nominal + u0_noise, -1.0, 1.0)

                # Initialize concentration field and time lists
                u = [u_init]
                t = [0.0]

                # Initialize the simulator with the initial concentration field
                simulator.initialize(u=u[0])

                # Run the simulation for the specified number of steps
                for _ in range(experiment_durations[mode]):
                    u.append(simulator.step())  # Update concentration field
                    t.append(simulator.t)       # Record the current time

                # Stack the concentration fields into a 3D array
                u = np.stack(u, axis=0)
                t = np.array(t)  # Convert time list to numpy array

                # Create a group in the HDF5 file for this run
                run_group = h5f.create_group(f'run_{ii}')
                run_group.create_dataset('x_coordinates', data=simulator.X)
                run_group.create_dataset('y_coordinates', data=simulator.Y)
                run_group.create_dataset('field_values', data=u)
                run_group.create_dataset('time', data=t)
                run_group.create_dataset('length', data=len(t))

if __name__ == "__main__":
    # Argument parser
    parser = argparse.ArgumentParser(description='Generate training, validation, and test datasets using the simulator.')

    # Dataset parameters
    parser.add_argument('--dt', type=float, default=1e-2, help='Integrator time step')
    parser.add_argument('--n_steps_train', type=int, default=500, help='Number of time steps per simulation')
    parser.add_argument('--n_steps_test', type=int, default=1000, help='Number of time steps per simulation')
    parser.add_argument('--n_train', type=int, default=50, help='Number of simulations for training')
    parser.add_argument('--n_valid', type=int, default=10, help='Number of simulations for validation')
    parser.add_argument('--n_test', type=int, default=50, help='Number of simulations for testing')
    parser.add_argument('--init_noise_scale', type=float, default=0.1, help='noise scale for uniform random initial condition')

    # Parse arguments and run main function
    args = parser.parse_args()
    main(args)
