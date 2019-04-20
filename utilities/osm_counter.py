import xml.etree.ElementTree as et
import operator

f = open("C:/GIS_DATA/Pittsburgh/vectors/osm/stats.txt","w")

tree = et.parse("C:/GIS_DATA/Pittsburgh/vectors/osm/map.osm")
root = tree.getroot()
nodes = {}
ways = {}
relations = {}
bounds = None

# This is becoming extremly confusing so I'm creating a class
class counted_tag:
    def __init__(self,tag_name):
        self.tag_name = tag_name
        self.tag_count = 0
        self.unique_value_counts = {}

# build ID dicts in memory
for element in root:
    if element.tag == 'node':
        nodes[int(element.get('id'))] = element
    elif element.tag == 'way':
        ways[int(element.get('id'))] = element
    elif element.tag == 'relation':
        relations[int(element.get('id'))] = element
    elif element.tag == 'bounds':
        bounds = element
    else:
        print("Found unused element called: " + element.tag)

# using these, we can parse ways and relations rapidly I guess.
# print a list of all the node tags in use
def incr_dict_element(dic,key):
    if not key in dic:
        dic[key] = 1
    else:
        dic[key] = dic[key] + 1

def incr_dict_k_v(dic,key,value):
    if not key in dic:
        dic[key] = {value:1}
    else:
        if not value in dic[key].keys():
            dic[key][value] = 1
        else:
            dic[key][value] = dic[key][value] + 1

# https://stackoverflow.com/questions/613183/how-do-i-sort-a-dictionary-by-value
def sort_my_dict(dic):    
    return sorted(dic.items(),key=operator.itemgetter(1),reverse=True)


types = (nodes, ways, relations)
for typie in types:
    # Assemble Dict (tags) of Dicts (values : their counts)
    tags = {}
    print("Total: ", len(typie),file=f)
    for node_id in typie:
        node = typie[node_id]
        for tag in node.iter('tag'):        
            incr_dict_k_v(tags,tag.get('k'),tag.get('v'))            
    # Do Tallys for each tag
    for values in tags:        
        vcd = sort_my_dict(tags[values])
        
        #create tally
        tally = 0
        for v in vcd:
            tally = tally + int(v[1])
            
        #Add tally as a counted value, so we can use it to sort values        
        print(values + " " + str(tally) ,file=f)
        
        for v in vcd:            
            f.write(str(v[1]))
            f.write(" ")
            f.write("  ")            
            f.write(str(v[0].encode('utf-8', 'ignore')))
            f.write("\n")            
        print("   .....................................................",file=f)
    print("======================================================",file=f)
    
f.close()
