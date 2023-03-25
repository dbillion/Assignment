import json
import sys
import re


def generate_schedule(squads, patrol_start, patrol_end):
    # Convert patrol start and end times to hours
    [patrol_start, patrol_end_hour] = map(int, (patrol_start.split(':')[0], patrol_end.split(':')[0]))
    patrol_end_hour += 24 if patrol_end_hour < patrol_start else 0
    patrol_hours = patrol_end_hour - patrol_start

    # Determine the number of squads and soldiers in each squad
    num_squads = len(squads)
    squad_size = [len(squad) for squad in squads]

    # Divide patrol hours equally among squads
    patrol_hours_per_squad = patrol_hours // num_squads

    # Assign two members from the same squad to each patrol shift
    patrol_schedule = []
    for squad in range(num_squads):
        soldiers = list(range(squad_size[squad]))
        for hour in range(patrol_hours_per_squad):
            if len(soldiers) >= 2:
                soldier1, soldier2 = soldiers[:2]
                soldiers = soldiers[2:] + [soldier1, soldier2]
                patrol_schedule.append((squad, soldier1, soldier2))

    # Create a stove-watch schedule for each squad
    stove_watch_schedule = []
    for squad in range(num_squads):
        soldiers = list(range(squad_size[squad]))
        for hour in range(6):
            if len(soldiers) > 0:
                soldier = soldiers.pop(0)
                stove_watch_schedule.append((squad, soldier))
                soldiers.append(soldier)

    # Make sure drivers have 6 hours of consecutive sleep time
    def check_sleep_time(schedules, squad, driver):
        sleep_time = 0
        for hours in range(6):
            if (squad, driver) not in schedules[hours]:
                sleep_time += 1
            else:
                sleep_time = 0
            if sleep_time >= 6:
                return True
        return False

    patrol_schedule_by_hour = [[] for _ in range(6)]
    for squad, soldier1, soldier2 in patrol_schedule:
        patrol_schedule_by_hour[soldier1 // 2].append([squad, soldier1])
        patrol_schedule_by_hour[soldier1 // 2].append([squad, soldier2])

    stove_watch_schedule_by_hour = [[] for _ in range(6)]
    for squad, soldier in stove_watch_schedule:
        stove_watch_schedule_by_hour[soldier].append([squad, soldier])

    all_schedules = [patrol_schedule_by_hour[i] + stove_watch_schedule_by_hour[i] for i in range(6)]

    drivers_sleep_time_ok = True
    for squad in range(num_squads):
        driver_index = 0
        for soldier_index, soldier in enumerate(squads[squad]):
            if soldier['driver']:
                if not check_sleep_time(all_schedules, squad, soldier_index):
                    drivers_sleep_time_ok = False
                    break
                driver_index += 1

    if not drivers_sleep_time_ok:
        return None

    # Format schedule as JSON
    schedule_json = {'patrols': [], 'stove_watch': []}
    for squad, soldier1, soldier2 in patrol_schedule:
        schedule_json['patrols'].append({
            'squad': squad + 1,
            'soldiers': [squads[squad][soldier1]['name'], squads[squad][soldier2]['name']]
        })
    for squad, soldier in stove_watch_schedule:
        schedule_json['stove_watch'].append({
            'squad': squad + 1,
            'soldier': squads[squad][soldier]['name']
        })

    return schedule_json


def main():
    # Check if input file is provided as command line argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        with open(input_file) as f:
            lines = f.read().splitlines()

        # Parse input from file
        patrol_start, patrol_end = lines.pop(0).split(' - ')
        squads = []
        current_squad = []
        for line in lines:
            if line.strip() == '':
                squads.append(current_squad)
                current_squad = []
            else:
                match = re.match(r'(\w+)\. (\w+)(?: \((Driver)\))?', line)
                if match:
                    rank, name, driver = match.groups()
                    current_squad.append({
                        'rank': rank,
                        'name': name,
                        'driver': driver == 'Driver'
                    })
        squads.append(current_squad)
    else:
        # Get input from command line
        patrol_start, patrol_end = map(str.strip,
                                       input('Enter patrol start and end times (e.g., 20:00 - 06:00): ').split('-'))
        squads = []
        current_squad = []
        while True:
            line = input(
                "Enter soldier information (rank name driver), an empty line to start a new squad, or \"done\" to "
                "finish: ")
            if line.strip() == '':
                squads.append(current_squad)
                current_squad = []
            elif line.strip() == 'done':
                squads.append(current_squad)
                break
            else:
                parts = line.split()
                rank, name = parts[:2]
                driver = parts[2] if len(parts) > 2 else ''
                current_squad.append({
                    'rank': rank,
                    'name': name,
                    'driver': driver == 'driver'
                })

    # Generate schedule
    schedule_json = generate_schedule(squads, patrol_start, patrol_end)

    # Output schedule
    if schedule_json is None:
        print('No valid schedule found')
    else:
        print(json.dumps(schedule_json, indent=4))
        # Ask user if they want to save the output
        save_output = input("Do you want to save the output as a file? (y/n): ")
        # Save output to file if user wants to
        if save_output.lower() == 'y':
            # Ask user for the name of the file
            file_name = input("Enter the name of the file (without extension): ")
            # Add .json extension to the file name
            file_name += ".json"
            with open(file_name, 'w') as f:
                # Convert schedule_json from a dictionary to a JSON-formatted string
                schedule_json_str = json.dumps(schedule_json, indent=4)
                # Write the JSON-formatted string to the file
                f.write(schedule_json_str)


if __name__ == '__main__':
    main()
