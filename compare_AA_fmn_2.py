import random
from datetime import datetime

import torch
import numpy as np
import matplotlib.pyplot as plt
from autoattack.autoattack import AutoAttack

from torchvision import datasets, transforms

from Attacks.fmn_base import FMN as FMN_base
from Utils.fmn_strategies import fmn_strategies
from Utils.load_model import load_data

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_random_index(model, cifar_dataset):
    random_sample_index = None
    misclassified = True

    while misclassified:
        random_sample_index = random.randint(0, len(cifar_dataset) - 1)

        sample, label = cifar_dataset[random_sample_index]
        sample = sample.unsqueeze(0)

        y_pred = model(sample)
        y_pred = torch.argmax(y_pred)

        misclassified = (y_pred != label)
        if misclassified:
            print("Misclassified sample, changing...")

    return random_sample_index, sample, label


def compare_AA_fmn(
        model_id=8,
        steps=15,
        epsilon=None,
        loss='LL',
        optimizer='SGD',
        scheduler='CALR',
        gradient_strategy='Normalization',
        initialization_strategy='Standard',
        norm='Linf',
        AA_attack_to_run=('apgd-ce',),
        AA_n_restarts=1,
        AA_epsilon=8/255,
        exp_name='base',
        seed=42,
        alpha_init=1,
        alpha_final=None
):
    torch.manual_seed(seed)
    random.seed(seed)

    # model definition
    model, dataset, model_name, dataset_name = load_data(model_id=model_id)
    model.eval()
    model.to(device)

    # retrieving FMN set of configurations
    fmn_dict = fmn_strategies()

    cifar_dataset = datasets.CIFAR10(root='./Models/data', train=False, download=True, transform=transforms.ToTensor())

    random_sample_index, sample, label = get_random_index(model, cifar_dataset)

    label = torch.tensor([label,])
    print(f"Sample id: {random_sample_index}")

    # running autoattack
    adversary = AutoAttack(model, norm=norm, eps=AA_epsilon, version='standard', device=device, verbose=True)
    adversary.attacks_to_run = AA_attack_to_run
    adversary.apgd.n_restarts = AA_n_restarts
    adversary.apgd.n_iter = steps

    adversary.run_standard_evaluation(sample, label, bs=1)

    norm_to_num = {
        'Linf': float('inf'),
        'L2': 2,
        'L1': 1,
        'L0': 0
    }

    # running FMN
    strategy = fmn_dict['0']
    attack = FMN_base(model, steps=steps, loss=loss, device=device, epsilon=epsilon,
                      initialization_strategy=initialization_strategy, gradient_strategy=gradient_strategy,
                      scheduler=scheduler, optimizer=optimizer, norm=norm_to_num[norm], alpha_init=alpha_init,
                      alpha_final=alpha_final)

    adv_x, best_distance = attack.forward(sample, label)
    last_dist = attack.attack_data['distance'][-1]
    print(f"Last distance:\n{last_dist}")

    # Store AA and FMN losses
    loss_AA = -adversary.apgd.loss_total[-steps:]
    loss_fmn = attack.attack_data['loss'][-steps:]

    # plot losses
    fig, ax = plt.subplots(figsize=(4,4))

    steps_x = np.arange(0, steps)
    ax.plot(steps_x, loss_AA, label='AA loss')
    ax.plot(steps_x, [loss_indiv.detach().item() for loss_indiv in loss_fmn], label='FMN loss')

    ax.grid()
    ax.legend()

    # Get current date
    current_date = datetime.now()
    formatted_date = current_date.strftime("%d%m%y")
    fig.savefig(f"AA_FMN_loss_comparison_{formatted_date}_{exp_name}.pdf")

    return loss_fmn, loss_AA, random_sample_index


if __name__ == '__main__':
    _, _, prev_id = compare_AA_fmn(
        epsilon=8/255,
        loss='CE',
        # seed=40,
        # seed=1024,
        seed=950,
        exp_name='exploiting_AA_11_RLROP_SGD_100steps_inf_seed40',
        steps=30,
        optimizer='SGD',
        alpha_init=2,
        alpha_final=None,
        scheduler='RLROP'
    )
