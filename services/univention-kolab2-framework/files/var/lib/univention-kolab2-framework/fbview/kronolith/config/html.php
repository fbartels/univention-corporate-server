<?php
/**
 * CSS properties unique to Kronolith.
 * This file is parsed by css.php, and used to produce a stylesheet.
 *
 * $Horde: kronolith/config/html.php.dist,v 1.31 2004/04/02 17:45:43 chuck Exp $
 */

$css['.day']['color'] = 'white';
$css['.day']['background-color'] = '#444466';
$css['.day:hover']['color'] = 'yellow';

$css['.hour']['font-size'] = '11px';
$css['.hour']['font-weight'] = 'bold';

$css['.halfhour']['font-size'] = '8px';
$css['.halfhour']['font-weight'] = 'bold';
$css['.halfhour']['vertical-align'] = 'super';

$css['.event']['font-size'] = '11px';
$css['.event']['color'] = 'black';

$css['.legend']['color'] = &$css['.light']['color'];
$css['.legend']['font-size'] = '11px';

$css['.today']['border'] = '2px solid #444466';
$css['.today']['background-color'] = 'white';

$css['.monthgrid']['background-color'] = '#999999';
$css['.othermonth']['background-color'] = '#e7eeec';
$css['.weekend']['background-color'] = '#fff9ef';

/* border-color and background-color will always be overridden for the
 * *-eventbox classes */
$css['.block-eventbox']['border-width'] = '1px';
$css['.block-eventbox']['border-style'] = 'solid';
$css['.block-eventbox']['-moz-border-radius'] = '5px';
$css['.block-eventbox']['padding-left'] = '1px';

$css['.month-eventbox']['border-width'] = '1px';
$css['.month-eventbox']['border-style'] = 'solid';
$css['.month-eventbox']['-moz-border-radius'] = '5px';
$css['.month-eventbox']['padding-left'] = '1px';

$css['.week-eventbox']['border-width'] = '1px';
$css['.week-eventbox']['border-style'] = 'solid';
$css['.week-eventbox']['-moz-border-radius'] = '15px';
$css['.week-eventbox']['padding-left'] = '5px';

$css['.day-eventbox']['border-width'] = '1px';
$css['.day-eventbox']['border-style'] = 'solid';
$css['.day-eventbox']['-moz-border-radius'] = '15px';
$css['.day-eventbox']['padding-left'] = '5px';

$css['.legend-eventbox']['border-width'] = '1px';
$css['.legend-eventbox']['border-style'] = 'solid';
$css['.legend-eventbox']['-moz-border-radius'] = '5px';
$css['.legend-eventbox']['padding-left'] = '1px';

/* Busy time periods. */
$css['.busy']['background-color'] = '#FF0000';
$css['.busy']['cursor'] = 'default';

/* Unknown time periods. */
$css['.unknown']['background-color'] = '#D4D0C8';
$css['.unknown']['background-image'] = 'url(' . $registry->getParam('graphics', 'kronolith') . '/unknown-background.gif)';    /* unknown time periods */
$css['.unknown']['background-repeat'] = 'repeat-x';

/* Free time periods. */
$css['.free']['background-color'] = '#28B22B';
$css['.free']['color'] = '#FFFFFF';

$css['.selected-control'] = $css['.selected'];
$css['.selected-control']['border-bottom'] = $css['.control']['border-bottom'];
