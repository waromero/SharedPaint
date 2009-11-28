[application]
name = SharedPaint
mimetype = application/x-ag-shared-paint
extension = sharedpaint
files = SharedPaint.py gui.py doodle.py events.py help.html uniandes-logo.png COPYING.txt README_EN.txt

[commands]
Open = %(python)s SharedPaint.py  -a %(appUrl)s -v %(venueUrl)s -i %(connectionId)s
