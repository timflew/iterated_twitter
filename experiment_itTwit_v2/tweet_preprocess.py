import csv
import numpy as np
import matplotlib.pyplot as plt
import os
import random
import re

def main():

	

	# Load raw tweets text
	fold_name='semval'
	#file_name='tweet-a.tsv' # a is context rating
	file_name='tweet-b-actual.tsv' # b is message rating
	full_name=os.path.join(fold_name,file_name)
	tweet_text,tweet_label=load_tweets(full_name)

	# Select only neutral tweets
	filter_emotion=['neutral'] # only keep neutral tweets
	tweet_filter=filter_tweets(tweet_text,tweet_label,filter_emotion)

	# Delete any existing emoticons so we can add our own
	# That being said, since we're focusing on neutral tweets, baserate will probably be low
	remove_patterns=[':)',':-)',': )',':(',':-(',': (',':p',':P',';)',';p',':3']
	tweet_noface=strip_emoticons(tweet_filter,remove_patterns)

	# Add random emotions
	add_patterns=[[':)',':-)',': )'],[':(',':-(',': ('],['']]
	tweet_emoticon,tweet_emotion=add_emoticons(tweet_noface,add_patterns)

	# Convert to php code so we can convert it to sql
	fname='create_initial_tweets_'
	num_chain=9
	num_stim=50
	convert2phpsql(fname,tweet_noface,tweet_emoticon,tweet_emotion,num_chain,num_stim)

	return None




def load_tweets(fname):
	# Load raw tweets
	tweet_file=open(fname,'rU')
	
	tweet_read_raw=csv.reader(tweet_file,delimiter='	', quotechar='"')

	# remove urls
	tweet_read=[]
	for row in tweet_read_raw:
		row2=row
		no_url_tweet=re.sub(r'http:[a-zA-Z0-9\/.]* \b', '', row2[-1])
		no_url_tweet=re.sub(r'http:[a-zA-Z0-9\/.]*\b', '', no_url_tweet)
		row2[-1]=no_url_tweet
		tweet_read.append(row2)

	# Go through all annotations
	tweet_text_all={}
	labels=['positive','negative','objective','objective-OR-neutral','neutral']
	for row in tweet_read:
		tweet=row[-1] # negative indices generalize across a and b files
		lab=row[-2]
		if tweet not in tweet_text_all:
			tweet_text_all[tweet]=[0, 0, 0]

		# treat objective, neutral and objective-OR-neutral as the same
		ind_lab=labels.index(lab)
		if ind_lab<2:
			tweet_text_all[tweet][ind_lab]+=1
		else:
			tweet_text_all[tweet][2]+=1
	
	# For all tweets, identify as positive vs. negative vs. neutral based on the max. In case of tie, say None
	tweet_text=[]
	tweet_label=[]
	labels_sum=['positive','negative','neutral']
	total_count=[0,0,0]
	for tweet in tweet_text_all.keys():
		
		tweet_text.append(tweet)

		curr_rank=np.array(tweet_text_all[tweet])
		# If no most salient label
		if len(curr_rank[curr_rank==max(curr_rank)])>1:
			tweet_label.append(None)
		else:
			tweet_label.append(labels_sum[np.argmax(curr_rank)])
			total_count[np.argmax(curr_rank)]+=1

		#print labels_sum[np.argmax(curr_rank)] + '         ' + tweet[0:100] 
	
	print labels_sum
	print total_count

	return tweet_text,tweet_label




def filter_tweets(tweet_text,label,filter_emotion):
	# Select only tweets of certain label

	tweet_filter=[]
	for text,lab in zip(tweet_text,label):
	
		if lab in filter_emotion:
			tweet_filter.append(text)

	return tweet_filter




def strip_emoticons(tweet_text,remove_patterns):
	# Delete any existing emoticons so we can add our own
	tweet_noface=[]
	for tweet in tweet_text:
		tweet_strip=tweet
		for pat in remove_patterns:
			tweet_strip=tweet_strip.replace(pat,'')
		tweet_noface.append(tweet_strip)


	return tweet_noface




def add_emoticons(tweet_noface,add_patterns):
	# Add random emotions
	num_emo=len(add_patterns)
	num_tweet=len(tweet_noface)

	shuf_ind=[0,1,2]*int(np.ceil(float(num_tweet)/3))
	shuf_ind2=shuf_ind[0:num_tweet] # cut off for number of tweets
	random.shuffle(shuf_ind2)

	tweet_emoticon=[]

	# Assign emotion
	
	for tweet,emo_ind in zip(tweet_noface,shuf_ind2):
		emoticon=add_patterns[emo_ind]
		sel_emoticon=np.random.choice(emoticon)
		tweet_emoticon.append(sel_emoticon)

	return tweet_emoticon,shuf_ind2




def convert2phpsql(fname,tweet_noface,tweet_emoticon,tweet_emotion,num_chain,num_stim):
	# If the table does not exist, create it
	fname_table=fname+'Table.php'
	if os.path.exists(fname_table):
		ex="File "+fname_table+" exists"
		print ex
	else:
		create_sql_table(fname_table)

	# Fill the table
	fname_fill=fname+'Fill.php'
	if os.path.exists(fname_fill):
		ex="File "+fname_fill+" exists"
		print ex
	else:
		# Fill the sql table
		fill_sql_table(fname_fill,tweet_noface,tweet_emoticon,tweet_emotion,num_chain,num_stim)
		


	return None




def fill_sql_table(fname,tweet_noface,tweet_emoticon,tweet_emotion,num_chain,num_stim):
	# Fill sql table with start entries

	# select subset of num_stim tweets
	sub_ind=np.random.choice(range(0,len(tweet_noface)),size=num_stim,replace=False)
	print sub_ind
	tweet_noface=list( tweet_noface[i] for i in sub_ind)
	tweet_emoticon=list( tweet_emoticon[i] for i in sub_ind)
	tweet_emotion=list( tweet_emotion[i] for i in sub_ind)


	# create file
	file=open(fname,'w')
	file.write('<?php\n')

	file.write("include('config.php');\n")

	# Store all emoticons into an array
	file.write('$all_emoticon=array(')
	num_tweet=len(tweet_emotion)
	count=0
	for emo in tweet_emoticon:
		if count<(num_tweet-1):
			file.write('"'+emo+'"'+',')
		else:
			file.write('"'+emo+'"')
			file.write(");")
			file.write('\n')			
		count+=1

	# Store all emotions into an array
	file.write('$all_emotion=array(')
	num_tweet=len(tweet_emotion)
	count=0
	for emo in tweet_emotion:
		if count<(num_tweet-1):
			file.write('"'+str(emo)+'"'+',')
		else:
			file.write('"'+str(emo)+'"')
			file.write(");")
			file.write('\n')
		count+=1

	# Store all tweets into an array
	file.write('$all_tweets=array(')
	num_tweet=len(tweet_noface)
	count=0
	for tweet in tweet_noface:
		tweet=tweet.replace('"','')
		tweet=tweet.replace("'",'')
		if count<(num_tweet-1):
			file.write('"'+tweet+'"'+',\n')
		else:
			file.write('"'+tweet+'"')
			file.write(");")
			file.write('\n')
		count+=1

	file.write('\n')

	# Run sql inserts
	file.write('$status="wait";\n')
	file.write('for($ic=0;$ic<$numChain;$ic++){\n')
	file.write('	for($i=0;$i<count($all_tweets);$i++){\n')
	file.write("		$currChain='base'.strval($ic);\n")
	file.write('		$query="INSERT INTO iter_tweet (subj,exp_id,chain,iter,text_id,text_proc,emotion,emoticon,status)'
	' VALUES '
	'''('$currChain','$exp_id','$ic',0,'$i','$all_tweets[$i]', '$all_emotion[$i]','$all_emoticon[$i]','$status')";\n''');
	file.write("		echo $query;")
	file.write("		echo '<br>';")
	file.write("		mysql_query($query);\n")
	file.write('\n')
	file.write('	}\n')
	file.write('}\n')
	file.write('?>')
	file.close()
	return None


def create_sql_table(fname):
	# If the table does not exist, create it
	# Fields
	# 0) id-primary key
	# 1) subj-varchar(40)
	# 2) chain-int
	# 3) iter-int
	# 4) text_id-int
	# 5) text_obs-varchar(200) # Text presented to subject
	# 6) text_recalled-varchar(200) # Text recalled by subject
	# 7) text_proc-varchar(200) # Text that will be presented to next subject (after emoticons removed and readded)
	# 8) claim_time-datetime
	# 9) claimed_by-varchar(40)
	# 10) emotion-set of char ('pos','neg')
	# 11) emoticon-set of char 
	# 12) status-set of char ('complete','in-pro','wait','claimed')
	file=open(fname,'w')
	file.write('<?php')
	file.write('\n')
	file.write("include('config.php');\n")
	# create table
	# $val = mysql_query('select 1 from `table_name` LIMIT 1');
	file.write("$val = mysql_query('SELECT 1 from `iter_tweet` LIMIT 1');\n")
	file.write('if($val == FALSE) {\n')
	file.write("	$query='CREATE TABLE iter_tweet (id INT(8) UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"subj VARCHAR(40),"
		"exp_id VARCHAR(10),"
		"chain INT(3),"
		"iter INT(3),"
		"text_id INT(3),"
		"text_obs VARCHAR(200),"
		"text_recalled VARCHAR(200),"
		"text_proc VARCHAR(200),"
		"claim_time DATETIME,"
		"claimed_by VARCHAR(40),"
		"emotion VARCHAR(10),"
		"emoticon VARCHAR(10),"
		"status VARCHAR(20)"
		")';\n")
	file.write("	echo $query;\n")
	file.write('	mysql_query($query);\n')
	file.write('}\n')
	
	file.write('?>')
	file.close()





if __name__=='__main__':
	main()

