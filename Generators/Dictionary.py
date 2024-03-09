
def createContainer( ):
    """
    This method creates a container object which fields can be assigned
    dynamically.
    
    For instance, the object returned by this method will allow:
    
    obj = createContainer()
    obj.newAttribute = 'my new attribute value'
    """
    
    # Way to create temporary structure.
    return type( 'TempStruct' , ( object , ) , {} )



# UI Data

input = createContainer()
input.foot = True
input.leg = True
input.hips = True
input.spine = True
input.arm = True
input.shoudler = True
input.spineCount = 3

# -----------------------------------------------------------------Create Guides---------------------------------------------------
j_hipName= "Hips"
j_spineName= "Spine"
