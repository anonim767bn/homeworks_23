"""Module for calculating the last login of users and the percentage of email hosts."""

import json
import os
from datetime import datetime
from typing import Any

import error_classes as errors


def write(message: str | tuple[str], output_path: str) -> None:
    """Write message in json file.

    Args:
        message: str | tuple[str] - strings to write.
        output_path: str - file to write message.
    """
    dirname = os.path.dirname(output_path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(output_path, 'w') as output_file:
        json.dump(message, output_file)


def get_last_login(client: str, client_info: dict, output_path: str) -> str:
    """Find client email host.

    Args:
        client: str - client name.
        client_info: dict - info about client: region, registered, last_login, email, age.
        output_path: str - file to write

    Returns:
        str: last login date.

    Raises:
        NonExistentField: calls if client have not last_login field.
        EmptyField: calls if last_login field is empty.
    """
    try:
        last_login = client_info['last_login']
    except KeyError:
        raise errors.NonExistentField(client, 'last_login', output_path)
    if not last_login:
        raise errors.EmptyField(client, 'last_login', output_path)
    return last_login


def get_host(client: str, client_info: dict, output_path: str) -> str:
    """Find client email host.

    Args:
        client: str - client name.
        client_info: dict - info about client: region, registered, last_login, email, age.
        output_path: str - file to write

    Returns:
        str: name of email host.

    Raises:
        NonExistentField: calls if client have not email field.
        EmailError: calls if client have not correct email.
        EmptyField: calls if at client email does not exists host name.
    """
    try:
        host = client_info['email'].split('@')[1]
    except IndexError:
        raise errors.EmailError(client, output_path)
    except KeyError:
        raise errors.NonExistentField(client, 'email', output_path)
    if not host:
        raise errors.EmptyField(client, 'email', output_path)
    return host


def get_hosts_count(json_data: Any, output_path: str) -> dict:
    """Count the number of different hosts.

    Args:
        json_data: Any - loaded json file.
        output_path: str - file to write

    Returns:
        dict: email host and the number of times it appears among users.
    """
    hosts_count = {}
    for client, client_info in json_data.items():
        host = get_host(client, client_info, output_path)
        hosts_count[host] = hosts_count.get(host, 0) + 1
    return hosts_count


def change_online_status_counter(
    online_status_count: dict[str: int],
    client: str,
    client_info: dict,
    output_path: str,
        ) -> None:
    """Change online status counter using last login ago.

    Args:
        online_status_count: dict[str: int] - list with online statisctic.
        client: str - client name.
        client_info: dict - info about client: region, registered, last_login, email, age.
        output_path: str - file to write
    """
    date = datetime.strptime(get_last_login(client, client_info, output_path), '%Y-%m-%d')
    last_login_ago = (datetime.now() - date).days
    two_days = 2
    week = 7
    month = 30
    six_months = month * 6
    if last_login_ago < two_days:
        online_status_count['less_than_2_days'] += 1
    elif last_login_ago < week:
        online_status_count['less_than_a_week'] += 1
    elif last_login_ago < month:
        online_status_count['less_than_a_month'] += 1
    elif last_login_ago < (six_months):
        online_status_count['less_than_six_months'] += 1
    else:
        online_status_count['more_than_six_months'] += 1


def process_data(input_path: str, output_path: str) -> None:
    """Process the input_path and write statistics to output_path.

    Args:
        input_path: str - file with data for process.
        output_path: str - file to write statistics.

    Raises:
        NoInputFile: calls if input file not exists.
        ListNotExpected: calls if programm meet list in input file.
    """
    online_status_count = {
        'less_than_2_days': 0,
        'less_than_a_week': 0,
        'less_than_a_month': 0,
        'less_than_six_months': 0,
        'more_than_six_months': 0,
    }
    hosts_percentage = {}
    try:
        with open(input_path, 'r') as input_file:
            json_data = json.load(input_file)
    except FileNotFoundError:
        raise errors.NoInputFile(input_path, output_path)
    except json.JSONDecodeError:
        write('', output_path)
    try:
        for client, client_info in json_data.items():
            change_online_status_counter(online_status_count, client, client_info, output_path)
    except AttributeError:
        raise errors.ListNotExpected(output_path)
    for host_name, count in get_hosts_count(json_data, output_path).items():
        hosts_percentage[host_name] = round((count / len(json_data)) * 100, 2)
    write((online_status_count, hosts_percentage), output_path)
