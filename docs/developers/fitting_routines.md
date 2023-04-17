# overview

# ChannelCompatibilityCheck

# run method 

   First gets the parameter of interest and the RooSimultaneousPDf 
   
   Then loops over channels and gets the pdf for each channel
   then replaces the POI in each channel pdf with a new POI specific to that channel
   and adds this new channel pdf to a new SimultaneousPDF created for the full fit

   creates a `CascadeMimizer` object and 
