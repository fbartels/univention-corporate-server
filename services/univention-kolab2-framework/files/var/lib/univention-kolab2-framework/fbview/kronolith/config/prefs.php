<?php
/**
 * $Horde: kronolith/config/prefs.php.dist,v 1.52 2004/05/18 20:17:53 chuck Exp $
 *
 * See horde/config/prefs.php for documentation on the structure of this file.
 */

$prefGroups['view'] = array(
    'column' => _("Display Options"),
    'label' => _("User Interface"),
    'desc' => _("Select confirmation options, how to display the different views and choose default view."),
    'members' => array('confirm_delete', 'defaultview', 'half', 'time_between_days',
                       'week_start_monday', 'day_hour_start', 'day_hour_end',
                       'show_icons', 'show_legend', 'show_fb_legend', 'show_shared_side_by_side')
);

$prefGroups['summary'] = array(
    'column' => _("Display Options"),
    'label' => _("Portal Options"),
    'desc' => _("Select which events to show in the portal."),
    'members' => array('summary_days', 'summary_alarms')
);

$prefGroups['share'] = array(
    'column' => _("Calendars"),
    'label' => _("Shared Calendars"),
    'desc' => _("Create, edit, and delete calendars; also control the access of other users to calendars that you own."),
    'members' => array('shareselect')
);
if (Auth::getAuth()) {
    $prefGroups['share']['members'][] = 'share_link';
}

$prefGroups['remote'] = array(
    'column' => _("Calendars"),
    'label' => _("Remote Calendars"),
    'desc' => _("Manage remote calendars."),
    'members' => array('remote_cal_management')
);

if (isset($registry) && $registry->hasMethod('tasks/listTasks')) {
    $prefGroups['tasks'] = array(
        'column' => _("Display Options"),
        'label' => _("Tasks"),
        'desc' => _("Select to show due tasks in the calendar."),
        'members' => array('show_tasks')
    );
}

if (isset($registry) && $registry->hasMethod('meeting/list')) {
    $prefGroups['meetings'] = array(
        'column' => _("Display Options"),
        'label' => _("Meetings"),
        'desc' => _("Select to show meetings in the calendar."),
        'members' => array('show_meetings')
    );
}


// default view
$_prefs['defaultview'] = array(
    'value' => 'attendeesview',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array('day' => _("Day"),
                    'week' => _("Week"),
                    'workweek' => _("Work Week"),
                    'month' => _("Month"),
                    'attendeesview' => _("Free/Busy")),
    'desc' => _("Select the view to display on startup:")
);

// half hour slots
$_prefs['half'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show half hour slots in day and week views?")
);

// what day does the week start with
$_prefs['week_start_monday'] = array(
    'value' => '0',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'desc' => _("Select the first weekday:"),
    'enum' => array('0' => _("Sunday"),
                    '1' => _("Monday"))
);

// days to show in summary
$_prefs['summary_days'] = array(
    'value' => 7,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'desc' => _("Select the time span to show:"),
    'enum' => array(1 => '1 ' . _("day"),
                    2 => '2 ' . _("days"),
                    3 => '3 ' . _("days"),
                    4 => '4 ' . _("days"),
                    5 => '5 ' . _("days"),
                    6 => '6 ' . _("days"),
                    7 => '1 ' . _("week"),
                    14 => '2 ' . _("weeks"),
                    21 => '3 ' . _("weeks"),
                    28 => '4 ' . _("weeks"))
);

// show alarms in summary?
$_prefs['summary_alarms'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show only events that have an alarm set?")
);

// show due tasks in the calendar views?
$_prefs['show_tasks'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show due tasks in the calendar?")
);

// show meetings in the calendar views?
$_prefs['show_meetings'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show meetings in the calendar?")
);

// confirm deletion of events which don't recur?
$_prefs['confirm_delete'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Confirm deletion of events?")
);

// start of the time range in day/week views:
$_prefs['day_hour_start'] = array(
    'value' => 16,
    'locked' => false,
    'shared' => false,
    'type' => 'select',
    'desc' => _("What time should day and week views start, when there are no earlier events?")
);

// end of the time range in day/week views:
$_prefs['day_hour_end'] = array(
    'value' => 48,
    'locked' => false,
    'shared' => false,
    'type' => 'select',
    'desc' => _("What time should day and week views end, when there are no later events?")
);

// default calendar selection widget
$_prefs['shareselect'] = array('type' => 'special');

// default calendar
// Set locked to true if you don't want users to have multiple calendars.
$_prefs['default_share'] = array(
    'value' => Auth::getAuth() ? Auth::getAuth() : 0,
    'locked' => false,
    'shared' => true,
    'type' => 'implicit'
);

if (Auth::getAuth()) {
    $_prefs['share_link'] = array(
        'type' => 'link',
        'url' => 'calendars.php',
        'img' => 'kronolith.gif',
        'desc' => _("Edit your calendars.")
    );
}

// user calendar categories
$_prefs['event_categories'] = array(
    'value' => sprintf('1:%s|2:%s', _("Personal"), _("Business")),
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// category highlight colors
$_prefs['event_colors'] = array(
    'value' => '1:#dddddd|2:#ffffcc',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// number of days to generate free/busy information for:
$_prefs['freebusy_days'] = array(
    'value' => 30,
    'locked' => false,
    'shared' => false,
    'type' => 'number',
    'desc' => _("How many days into the future should we generate free/busy information for?")
);

// store the calendars to diplay
$_prefs['display_cals'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// show delete/alarm icons in the calendar view?
$_prefs['show_icons'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show delete, alarm, and recurrence icons in calendar views?")
);

// manage remote calendars
$_prefs['remote_cal_management'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'special',
    'desc' => _("Edit Remote Calendars")
);

// store the remote calendars to display
$_prefs['remote_cals'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// store the remote calendars to display
$_prefs['display_remote_cals'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// collapsed or side by side view
$_prefs['show_shared_side_by_side'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show shared calendars side-by-side")
);

// show category legend?
// a value of 0 = no, 1 = yes
$_prefs['show_legend'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show category legend?")
);

// show free/busy legend?
// a value of 0 = no, 1 = yes
$_prefs['show_fb_legend'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show free/busy legend?")
);

// display the timeslots between each day column, in week view
$_prefs['time_between_days'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show time of day between each day in week views?")
);

$_prefs['saved_attendee_list'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'text',
    'desc' => _("Saved Attendee List:")
);
