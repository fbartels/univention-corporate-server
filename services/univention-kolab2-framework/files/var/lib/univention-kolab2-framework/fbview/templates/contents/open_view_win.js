<script language="JavaScript" type="text/javascript">
<!--

function tr(badval)
{
    retval = '';
    validchars = 'abcdefghijklmnopqrstuvwxyz0123456789';

    badval.toLowerCase();
    for (i = 0; i < badval.length; i++) {
        if (validchars.indexOf(badval.charAt(i)) != -1) {
            retval += badval.charAt(i);
        } else {
            retval += '_';
        }
    }
    return retval;
}

function view(url, partid)
{
    param = "menubar=yes,toolbar=no,location=no,status=no,scrollbars=yes,resizable=yes";
    window.open(url, '<?php echo md5(mt_rand()) ?>' + tr(partid), param);
}

// -->
</script>
