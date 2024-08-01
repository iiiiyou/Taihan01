import multiprocessing
import util.format_date_time as ti
import insert_sqllite_area as area

def c_area(product, mean_avg, mean_masks):
	for i in range(len(mean_masks)):
		mean = mean + mean_masks[i]
	mean = mean/len(mean_masks)
	upmean_avg = mean_avg * 1.1
	dwmean_avg = mean_avg * 0.9
	c_time = ti.get_date_time()

	if(upmean_avg < mean or dwmean_avg > mean):
		area.write_sql(c_time, product, mean)
		
