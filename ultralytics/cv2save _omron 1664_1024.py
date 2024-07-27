import cv2
import ultralytics.format_date_time as date

from harvesters.core import Harvester
import sys
import traceback

h = Harvester()
h.add_file('C:\\Program Files\\Common Files\\OMRON_SENTECH\\GenTL\\v1_5\\StGenTL_MD_VC141_v1_5_x64.cti')
h.files
h.update()
h.device_info_list
print(h.device_info_list)

# ia = h.create(0)
# ia = h.create({'serial_number': '23G7076'}) # - 1080 camera left
# ia = h.create({'serial_number': '23G7069'}) # - 1080 camera right
ia = h.create({'serial_number': '22FK019'}) # - 1664 camera left

try:
    ia.start()
    i = 0
    done = False
    with ia.fetch() as buffer:
        # Work with the Buffer object. It consists of everything you need.
        print(buffer)
        # The buffer will automatically be queued.
        img = buffer.payload.components[0].data
        img = img.reshape(buffer.payload.components[0].height, buffer.payload.components[0].width)
        img_copy = img.copy()
        img_copy = cv2.cvtColor(img, cv2.COLOR_BayerRG2RGB)


        fps = ia.statistics.fps
        print("FPS: ", fps)

        
        cv2.imwrite('images\\training\\1664_'+date.get_time_in_mmddss()+'.jpg', img_copy)

        #########################  
        # Make folders if not exsist
        # path='detect_image\\'+date.format_date()+'\\'
        # makedirs(path)

        # Saving images
        # cv2.imwrite('detect_image\\'+date.format_date()+'\\'+date.get_time_in_mmddss()+'.jpg', annotated_frame)
        
        if cv2.waitKey(10) == ord('q'):
            done = True
            print('break')
        i = i + 1
except Exception as e:
    traceback.print_exc(file=sys.stdout)
finally:
    ia.stop()
    ia.destroy()
    cv2.destroyAllWindows()
    print('fin')
    h.reset()

h = Harvester()
h.add_file('C:\\Program Files\\Common Files\\OMRON_SENTECH\\GenTL\\v1_5\\StGenTL_MD_VC141_v1_5_x64.cti')
h.files
h.update()
h.device_info_list
print(h.device_info_list)

ia2 = h.create({'serial_number': '23G7069'}) # - 1080 camera right
# ia = h.create({'serial_number': '22FK019'}) # - 1664 camera left

try:
    ia2.start()
    i = 0
    done = False
    with ia2.fetch() as buffer:
        # Work with the Buffer object. It consists of everything you need.
        print(buffer)
        # The buffer will automatically be queued.
        img = buffer.payload.components[0].data
        img = img.reshape(buffer.payload.components[0].height, buffer.payload.components[0].width)
        img_copy = img.copy()
        img_copy = cv2.cvtColor(img, cv2.COLOR_BayerRG2RGB)


        fps = ia2.statistics.fps
        print("FPS: ", fps)

        
        cv2.imwrite('images\\training\\1024_'+date.get_time_in_mmddss()+'.jpg', img_copy)

        #########################  
        # Make folders if not exsist
        # path='detect_image\\'+date.format_date()+'\\'
        # makedirs(path)

        # Saving images
        # cv2.imwrite('detect_image\\'+date.format_date()+'\\'+date.get_time_in_mmddss()+'.jpg', annotated_frame)
        
        if cv2.waitKey(10) == ord('q'):
            done = True
            print('break')
        i = i + 1
except Exception as e:
    traceback.print_exc(file=sys.stdout)
finally:
    ia2.stop()
    ia2.destroy()
    cv2.destroyAllWindows()
    print('fin')
    h.reset()
