import sys
my_path = "C:\\Users\\SHARAN O KOTRE\\Desktop\\UMCP\\ENTS656\\ProjectScripts"
sys.path.append(my_path)

import numpy as np
import AdmissionControlUtils as acu

##constant parameter init
TRANSMITTER_HEIGHT = 50                                                            #Height of the transmitting antenna in meters.
MAX_TRANSMITTER_POWER_DBM = 42                                                     #Maximum power transmitted by the transmitting antenna - in dbm.
CONNECTOR_LOSSES_DB = 2.1                                                          #Connector Losses in db. Subtracted from the maximum power and the antenna gain.
TRANSMITTER_GAIN_DB = 12.1                                                         #Transmitter gain in db
CARRIER_FREQUENCY_MHZ = 1900                                                       #Carrier frequency in Mhz
CARRIER_BANDWIDTH = 1.25*(10**6)                                                   #Carrier Bandwidth in Hz
BIT_RATE = 12.5*(10**3)                                                            #Bit rate in kbps
NOISE_LEVEL_DBM = -110                                                             #Noise level in dbm  
REQUIRED_SINR_DB = 6                                                               #Required level of SINR to be maintained by users on a call.
MIN_PILOT_RSL_DBM = -107                                                           #Required RSL for the users to communicate with the basestation.  
CALL_ARRIVAL_RATE_PER_HOUR = 6                                                     #Average csll rate in hrs
AVERAGE_CALL_DURATION_SECONDS = 60                                                 #Average call duration in seconds
NUMBER_OF_USERS = 1000                                                             #Numbers of users in the cell area.
NUMBER_OF_TRAFFIC_CHANNELS = 56                                                    #Number of Traffic channels available.
EIRP = MAX_TRANSMITTER_POWER_DBM + TRANSMITTER_GAIN_DB - CONNECTOR_LOSSES_DB       #EIRP of the Transmitting Antenna.
PROCESSOR_GAIN_DB = CARRIER_BANDWIDTH/BIT_RATE                                     #Processor gain of the system.
TIME_INTERVAL_S = 1                                                                
EIRP_Pilot = EIRP                                                                  #EIRP_Pilot initially equals EIRP computed using MAX_TRANSMITTER_POWER_DBM.
                                                                                   #When admission control is being used, this is incremented or decremented
                                                                                   #by Delta_EIRP_Pilot.

##admission control parameters
Cd = 57                                                                            #Maximum number of channels in use above which EIRP_Pilot is decreased.
Ci = 0                                                                             #Minimum number of channels below which EIRP_Pilot is increased.  
Delta_EIRP_Pilot_db = 0.5                                                          #EIRP_Pilot is incremented/decremented by this value.


distance_from_bstn_active_users_m = np.array([])                                   #Numpy array to hold distances from basestaion of active users.
direction_from_bstn_active_users_rad = np.array([])                                #Numpy array to hold direction from basestaion of active users.
distance_from_bstn_call_attempt_users_m = np.array([])                             #Numpy array to hold distances from basestaion of users attempting a call.
direction_from_bstn_call_attempt_users_rad = np.array([])                          #Numpy array to hold direction from basestaion of users attempting a call.

##shadowing based on normal distribution for mean 0db and standard deviation 2db
shadowing_factor = np.random.normal(0,2,2000*2000)                                 #Drawn using the normal distribution with 0db mean and 2db standard deviation.
shadowing_factor.resize(2000,2000)                                                 #Resized to fit the cell with radius 10km.


##statistics parameters init
available_channels = NUMBER_OF_TRAFFIC_CHANNELS                                  
active_users = np.array([],dtype=int)                                              #Numpy array to hold the active users
call_attempt_users = np.array([],dtype=int)                                        #Numpy array to hold the users attempting a call 
inactive_users = np.arange(NUMBER_OF_USERS)                                        #Numpy array to hold the inactive users
call_lengths = np.array([])                                                        #Numpy array to hold the call duration of active users  
number_of_calls_completed = 0                                                      #Successfully completed calls
number_of_calls_blocked_signal_strength = 0                                        #Blocked calls due to low signal strength for 3 consecutive seconds
number_of_calls_blocked_capacity = 0                                               #Blocked calls due to channel capacity
number_of_dropped_calls = 0                                                        #Dropped calls due to low SINR for 3 consecutive seconds
number_of_call_attempts_without_retries = 0                                        #Number of attempts not including retries.
number_of_call_attempts_retries = 0                                                #Number of retry attemps 
number_of_successful_connection = 0                                                #Number of successful connection to basestaion.
number_of_calls_in_progress = 0                                                    #Number of calls in progress.
number_of_failed_calls = 0                                                         #Number of failed calls
cell_radius_m = 0                                                                  #The distance from basestation of the most distant user in the cell.   
user_range = range(0,NUMBER_OF_USERS)        
rsl_counter = dict.fromkeys(user_range,0)                                          #Counter to keep track of the time at which attempting users fail the rsl test. 
sinr_counter = dict.fromkeys(user_range,0)                                         #Counter to keep track of the time at which active users fail the sinr test.    

##function to print statistics at any given time
def printStatistics(time):
    print('*********************************************************************************************')
    print('STATISTICS AT TIME: {0:d} seconds'.format(time))
    print('Number of call attempts not counting retries: ',number_of_call_attempts_without_retries)
    print('Number of call attempts counting retries: ',number_of_call_attempts_retries+number_of_call_attempts_without_retries)
    print('Number of calls dropped: ',number_of_dropped_calls)
    print('Number of calls blocked due to signal strength: ',number_of_calls_blocked_signal_strength)
    print('Number of calls blocked due to capacity: ',number_of_calls_blocked_capacity)
    print('Number of calls successfully completed: ',number_of_calls_completed)
    print('Number of calls in progress: ',NUMBER_OF_TRAFFIC_CHANNELS - available_channels)
    print('Number of calls failed: ',number_of_failed_calls)
    print('Current cell radius: {0}km'.format(cell_radius_m/1000))
    print('Number of available channels: ',available_channels)
    print('*********************************************************************************************')

##simulation begins here
for k in range(1,7201):
    ##processing call lengths for each active user
    if len(active_users)>0 and len(call_lengths) == len(active_users):
        
        call_lengths = call_lengths - TIME_INTERVAL_S ##decrementing the call length of each active users
        completed_calls_indices = np.where(call_lengths == 0)
        ongoing_calls_indices = np.where(call_lengths > 0)
        ##updating the number of calls completed followed by giving the channel back and moving the user from active pool to inactive pool
        number_of_calls_completed = number_of_calls_completed+len(active_users[completed_calls_indices])
        if available_channels+len(active_users[completed_calls_indices])>NUMBER_OF_TRAFFIC_CHANNELS:
            available_channels = NUMBER_OF_TRAFFIC_CHANNELS
        else:
            available_channels=available_channels+len(active_users[completed_calls_indices])
        inactive_users = np.append(inactive_users,active_users[completed_calls_indices])
        active_users = np.delete(active_users,completed_calls_indices)
        call_lengths = np.delete(call_lengths,completed_calls_indices)
        distance_from_bstn_active_users_m = np.delete(distance_from_bstn_active_users_m,completed_calls_indices)
        direction_from_bstn_active_users_rad = np.delete(direction_from_bstn_active_users_rad,completed_calls_indices)
        if len(distance_from_bstn_active_users_m):
            cell_radius_m = max(distance_from_bstn_active_users_m) #determining the cell radius.     
        
        if len(active_users)>0:
            ##monitoring sinr of each active user.
            fading_active_users_db = acu.getFading(len(active_users))
            path_loss_active_users_db = acu.getPathLoss(distance_from_bstn_active_users_m/1000)
            (i,j) = acu.getShadowingIndices(distance_from_bstn_active_users_m*np.cos(direction_from_bstn_active_users_rad),distance_from_bstn_active_users_m*np.sin(direction_from_bstn_active_users_rad))
            shadowing_active_users_db = shadowing_factor[np.array(i),np.array(j)]
            rsl_active_users_db = EIRP - path_loss_active_users_db + shadowing_active_users_db + fading_active_users_db
            sinr_active_users_db = acu.getSINR(rsl_active_users_db,len(active_users))
            sinr_below_min_active_users_indices = np.where(sinr_active_users_db < REQUIRED_SINR_DB)
            sinr_below_min_active_users = active_users[sinr_below_min_active_users_indices]
            ##updating a sinr_counter dictionary with the timestamp for the users who have failed the sinr test for the first time.
            ##For the users who have failed sinr test for 3 consecutive attempts, dropping the call and sending the user back to inactive pool after giving the channel back.
            for user in sinr_below_min_active_users:
                if sinr_counter[user]>0:
                    if (k-sinr_counter[user]) >= 2:  
                        number_of_dropped_calls=number_of_dropped_calls + 1
                        if available_channels + 1 > NUMBER_OF_TRAFFIC_CHANNELS:
                            available_channels = NUMBER_OF_TRAFFIC_CHANNELS
                        else:
                            available_channels = available_channels + 1
                        sinr_counter[user] = 0
                        inactive_users = np.append(inactive_users,[user])
                        call_lengths = np.delete(call_lengths,np.where(active_users == user))
                        distance_from_bstn_active_users_m = np.delete(distance_from_bstn_active_users_m,np.where(active_users == user))
                        direction_from_bstn_active_users_rad = np.delete(direction_from_bstn_active_users_rad,np.where(active_users == user))
                        active_users = np.delete(active_users,np.where(active_users == user))
                elif sinr_counter[user]==0:
                    sinr_counter[user] = k
      
    ##monitoring inactive users to see if they make a call attempt.
    inactive_user_calling_probability = np.random.poisson(1/600,size=len(inactive_users))

    ##moving all users who are determined to be making a call to the call_attempt_users array. 
    call_attempt_users_indices = np.where(inactive_user_calling_probability == 1)
    call_attempt_users = np.append(call_attempt_users,inactive_users[call_attempt_users_indices])

    ##incrementing the number of calls attempted without retries and deleting the users who are making a call from the inactive list.
    number_of_call_attempts_without_retries = number_of_call_attempts_without_retries + len(inactive_users[call_attempt_users_indices])
    inactive_users = np.delete(inactive_users,call_attempt_users_indices)
    
    if len(call_attempt_users)>0:
        ##finding out the location, computing path loss, looking up the shadowing value and computing fading for the users who are attempting a call.
        distance_from_bstn_call_attempt_users_m = acu.getDistances(len(call_attempt_users))
        direction_from_bstn_call_attempt_users_rad = acu.getDirection(len(call_attempt_users))
        path_loss_call_attempt_uses_db = acu.getPathLoss(distance_from_bstn_call_attempt_users_m/1000)
        fading_call_attempt_users_db = acu.getFading(len(call_attempt_users))
        (i,j) = acu.getShadowingIndices(distance_from_bstn_call_attempt_users_m*np.cos(direction_from_bstn_call_attempt_users_rad),distance_from_bstn_call_attempt_users_m*np.sin(direction_from_bstn_call_attempt_users_rad))
        shadowing_call_attempt_users_db = shadowing_factor[np.array(i),np.array(j)]

        ##computing the rsl of the users attempting the call. The EIRP_Pilot is varied by admission control algorithm
        ##based on the available channels continuosly when using admission control.
        rsl_call_attempt_users_db = EIRP_Pilot - path_loss_call_attempt_uses_db + shadowing_call_attempt_users_db + fading_call_attempt_users_db

        rsl_less_than_allowed_indices = np.where(rsl_call_attempt_users_db<MIN_PILOT_RSL_DBM)
        rsl_below_min_call_attempt_users = call_attempt_users[rsl_less_than_allowed_indices]
        ##updating a dictionary rsl_counter for users who have failed the rsl test.
        ## If the user fails the test for 3 consecutive seconds, the call is blocked and the number of blocked calls along with number of retries are inremented.
        for user in rsl_below_min_call_attempt_users:
                if rsl_counter[user]>0:
                    if (k-rsl_counter[user])>=2:
                        number_of_call_attempts_retries = number_of_call_attempts_retries+1
                        number_of_calls_blocked_signal_strength = number_of_calls_blocked_signal_strength + 1
                        rsl_counter[user] = 0
                        
                        if len(inactive_users[np.where(inactive_users == user)]) == 0:
                            inactive_users = np.append(inactive_users,[user])
                        else:
                            inactive_users = np.delete(inactive_users,np.where(inactive_users == user))
                            inactive_users = np.append(inactive_users,[user])
                        rsl_call_attempt_users_db = np.delete(rsl_call_attempt_users_db,np.where(call_attempt_users == user))
                        call_attempt_users = np.delete(call_attempt_users,np.where(call_attempt_users == user))
                        
                    elif (k-rsl_counter[user])< 2 and (k-rsl_counter[user])>0:
                        number_of_call_attempts_retries = number_of_call_attempts_retries + 1
                elif rsl_counter[user] == 0:
                    rsl_counter[user] = k

        #identifying the users who have passed the rsl test.
        rsl_call_connected_users_indices = np.where(rsl_call_attempt_users_db>=MIN_PILOT_RSL_DBM)
        if len(call_attempt_users[rsl_call_connected_users_indices])>0:
            if available_channels>0 and available_channels<=NUMBER_OF_TRAFFIC_CHANNELS:
                ##checking if there are enough channels available in the system. If true, allocate few of the channels for the attempting users
                if available_channels>len(call_attempt_users[rsl_call_connected_users_indices]):
                    distance_from_bstn_active_users_m = np.append(distance_from_bstn_active_users_m,distance_from_bstn_call_attempt_users_m[rsl_call_connected_users_indices])
                    direction_from_bstn_active_users_rad = np.append(direction_from_bstn_active_users_rad,direction_from_bstn_call_attempt_users_rad[rsl_call_connected_users_indices])
                    ##users now are added to active_users pool and their call lengths are determined. Their sinr will be monitored continuosly. The number of channels is decremented.
                    active_users = np.append(active_users,call_attempt_users[rsl_call_connected_users_indices])
                    if available_channels - len(call_attempt_users[rsl_call_connected_users_indices])<0:
                        available_channels = 0
                    else:
                        available_channels = available_channels - len(call_attempt_users[rsl_call_connected_users_indices])
                    number_of_successful_connection = number_of_successful_connection + len(call_attempt_users[rsl_call_connected_users_indices])
                    call_lengths_connected_users_s = np.ceil(np.random.exponential(AVERAGE_CALL_DURATION_SECONDS,len(call_attempt_users[rsl_call_connected_users_indices])))
                    call_lengths = np.append(call_lengths,call_lengths_connected_users_s)
                    call_attempt_users = np.delete(call_attempt_users,rsl_call_connected_users_indices)
                    distance_from_bstn_call_attempt_users_m = np.delete(distance_from_bstn_call_attempt_users_m,rsl_call_connected_users_indices)
                    direction_from_bstn_call_attempt_users_rad = np.delete(direction_from_bstn_call_attempt_users_rad,rsl_call_connected_users_indices)
                ##if not enough channels are available then channels are given to only a few users until there are no more channels left to give.
                elif available_channels <= len(call_attempt_users[rsl_call_connected_users_indices]):
                    distance_from_bstn_active_users_m = np.append(distance_from_bstn_active_users_m,distance_from_bstn_call_attempt_users_m[rsl_call_connected_users_indices][:available_channels])
                    direction_from_bstn_active_users_rad = np.append(direction_from_bstn_active_users_rad,direction_from_bstn_call_attempt_users_rad[rsl_call_connected_users_indices][:available_channels])
                    ##users who have been allotted a channel are now added to the active_users pool and their call lengths are determined.
                    ##Their sinr will be monitored continuosly. The number of channels is decremented. 
                    active_users = np.append(active_users,call_attempt_users[rsl_call_connected_users_indices][:available_channels])
                    call_lengths_connected_users_s = np.ceil(np.random.exponential(AVERAGE_CALL_DURATION_SECONDS,len(call_attempt_users[rsl_call_connected_users_indices][:available_channels])))
                    call_lengths = np.append(call_lengths,call_lengths_connected_users_s)
                    number_of_successful_connection = number_of_successful_connection + available_channels
                    if available_channels - len(call_attempt_users[rsl_call_connected_users_indices][:available_channels])<0:
                        available_channels = 0
                    else:
                        available_channels = available_channels - len(call_attempt_users[rsl_call_connected_users_indices][:available_channels])
                    ##The remaining users are blocked from making a call as the channel capacity is full.
                    ##They are added back to the inactive_users array to monitor if they attempt to make a call again.
                    ##They are also removed from call_attempt_users array.
                    inactive_users = np.append(inactive_users,call_attempt_users[rsl_call_connected_users_indices][available_channels+1:])
                    number_of_calls_blocked_capacity = number_of_calls_blocked_capacity + len(call_attempt_users[rsl_call_connected_users_indices][available_channels+1:])
                    call_attempt_users = np.delete(call_attempt_users,rsl_call_connected_users_indices[available_channels+1:])
                    distance_from_bstn_call_attempt_users_m = np.delete(distance_from_bstn_call_attempt_users_m,rsl_call_connected_users_indices[available_channels+1:])
                    direction_from_bstn_call_attempt_users_rad = np.delete(direction_from_bstn_call_attempt_users_rad,rsl_call_connected_users_indices[available_channels+1:])
            else:
                ##If no channels are available for the users making a call, then the calls are blocked and number
                ##of blocked call due to channel capacity is increased by the number of users blocked.
                inactive_users = np.append(inactive_users,call_attempt_users)
                number_of_calls_blocked_capacity = number_of_calls_blocked_capacity + len(call_attempt_users)
                call_attempt_users = np.array([],dtype=int)

    ##determining number of failed calls after every second
    number_of_failed_calls = number_of_calls_blocked_signal_strength + number_of_calls_blocked_capacity + number_of_dropped_calls

    ##Admission control: Depending on the number of channels in use, the
    ##admission control algorithm varies the EIRP_Pilot by +/- 0.5db every second.
    if NUMBER_OF_TRAFFIC_CHANNELS-available_channels > Cd:
        if EIRP_Pilot - Delta_EIRP_Pilot_db >= 30:
            EIRP_Pilot = EIRP_Pilot - Delta_EIRP_Pilot_db
    elif NUMBER_OF_TRAFFIC_CHANNELS-available_channels < Ci:
        if EIRP_Pilot + Delta_EIRP_Pilot_db <= EIRP:
            EIRP_Pilot = EIRP_Pilot + Delta_EIRP_Pilot_db        
    ##printing out statistics every 2 minutes of simulation time.   
    if k%120 == 0:
        printStatistics(k)
    
