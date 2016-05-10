#!/usr/bin/env python
"""

@author    :  Shane Bradley
@contact   :  sbradley@redhat.com
@version   :  0.1
@copyright :  GPLv3
"""
MAIN_LOGGER_NAME = "glocktop_analyze"
MAIN_LOGGER_FORMAT = "%(levelname)s %(message)s"

from datetime import datetime
def group_snapshots(snapshots, max_time_difference=10):
    # Returns map of snapshots grouped together. The key is the group count
    # and value is a list of snapshots that were taken around the same time.
    sorted_snapshots = sorted(snapshots, key=lambda x: x.get_date_time(), reverse=False)
    def get_time_difference(dt1, dt2):
        # dt1 is date_time that is newest and dt2 is the date_time that is oldest.
        return int((dt1 -dt2).total_seconds())

    if (sorted_snapshots):
        group_index = 1
        # Create the first group if there is a snapshot because no reason to
        grouped_snapshots = {1:[]}
        for snapshot in sorted_snapshots:
            # Base time to compare snapshot times.
            base_date_time = snapshot.get_date_time()
            current_group = grouped_snapshots.get(group_index)
            if (current_group):
                base_date_time = grouped_snapshots.get(group_index)[0].get_date_time()
            # Check to see if a new group should be created or if we need to
            # add to existing one.
            create_new_group = False
            for snapshot_in_group in grouped_snapshots.get(group_index):
                sg_hostname = snapshot_in_group.get_hostname()
                if (snapshot.get_hostname() == sg_hostname):
                    # If a host already has snapshot in there then do not
                    # add to current one.
                    create_new_group = True
                elif (get_time_difference(snapshot.get_date_time(),
                                          base_date_time) > max_time_difference):
                    # If the difference in greater than max difference then
                    # create a new group.
                    create_new_group = True
            if (create_new_group):
                group_index += 1
                grouped_snapshots[group_index] = [snapshot]
            else:
                grouped_snapshots[group_index].append(snapshot)
    return grouped_snapshots
