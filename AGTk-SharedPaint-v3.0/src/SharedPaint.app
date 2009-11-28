[application]
name = SharedPaint 3.0
mimetype = application/x-ag-shared-paint-3
extension = sharedpaint-3
files = Controller.py Messaging.py Model.py SharedPaint.py View.py Exceptions.py pen.png annotations_clear.gif image_clear.gif image_load.gif session_load.gif session_snapshot.gif sharedpaint_start.png sharedpaint_about.png COPYING.txt README_EN.txt README_ES.txt

[commands]
Open = %(python)s SharedPaint.py  -a %(appUrl)s -i %(connectionId)s
