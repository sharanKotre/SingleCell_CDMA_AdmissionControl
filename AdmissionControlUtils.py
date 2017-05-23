import numpy as np

CARRIER_FREQUENCY = 1900          #carrier frequency in Mhz
TRANSMITTER_HEIGHT = 50           #transmitter antenna height in m
CELL_RADIUS_M = 10000             #cell radius in meters
BW = 1.25*(10**6)                 #channel bandwidth in Hz
BIT_RATE = 12.5*(10**3)           #bit rate in bps
PROCESSOR_GAIN = (BW/BIT_RATE)    #processor gain linear

#function to compute the sinr. param1: Received signal levels. param2: number of users for which sinr needs to be calculated.
def getSINR(rsl,number_of_users):
    noise_level = -110
    if number_of_users>1:
        interference_level = rsl + (linearToDb(number_of_users - 1))
        linearNoisePlusIntereference = dbToLinear(interference_level)+dbToLinear(noise_level)
    elif number_of_users == 1: 
        linearNoisePlusIntereference = dbToLinear(noise_level)
    signal_level = rsl + linearToDb(PROCESSOR_GAIN)
    sinr = signal_level - linearToDb(linearNoisePlusIntereference)    
    return sinr

#function to compute the path loss based on the distance from basestation of the user using the COST231 Model. param1: distances from basestaion.
def getPathLoss(dist_from_bstn):
    path_loss_db = 46.3 + (33.9*np.log10(CARRIER_FREQUENCY)) - (13.82*np.log10(TRANSMITTER_HEIGHT)) + ((44.9-(6.55*np.log10(TRANSMITTER_HEIGHT)))*np.log10(dist_from_bstn))
    return path_loss_db

#function to compute the fading values based on the rayleigh distribution. param1: number of users for which the fading needs to be calculated.
def getFading(number_of_users):
    fading = np.random.rayleigh(1,number_of_users)
    fading2 = fading**2
    return linearToDb(fading2)

#function to convert from db to linear
def dbToLinear(db):
    linear = 10**(db/10)
    return linear

#function to convert from linear to db
def linearToDb(linear):
    db = 10*np.log10(linear)
    return db

#function to find out the distances of users from basestation based on uniform distribution.
def getDistances(num_users):
    return np.random.uniform(0,CELL_RADIUS_M,num_users)

#function to find out the direction of users from basestation based on uniform distribution.
def getDirection(num_users):
    return np.random.uniform(0,2*np.pi,num_users)

#function to find out the indices from which shadowing values can be accessed.
def getShadowingIndices(x,y):
    (i,j) = ([],[])
    
    for k in range(0,len(x)) :
        if x[k] >= 0:
            newX = x[k]//10
            if newX >= 1000:
                newX = newX - 1
            j.append(1000 + newX)
        elif x[k] < 0:
            newX = x[k]//10
            j.append(1000 - (abs(newX)))
        if y[k] >= 0:
            i.append(1000 - (y[k]//10))
        elif y[k] < 0:
            newY = y[k]//10
            if abs(newY) >= 1000:
                newY = abs(newY)-1
            i.append(1000 + (abs(newY)))
    return ([int(k) for k in i],[int(l) for l in j])


