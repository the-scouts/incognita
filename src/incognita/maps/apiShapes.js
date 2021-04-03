const chunkArr = (arr, chunkSize  = 50) => {
    let i = 0, arr_len = arr.length, groups = []
    while (i < arr_len) groups.push(arr.slice(i, i += chunkSize))
    return groups
}
const arrToFilterParam = arr => ({where: `${codeCol} IN ('${arr.join("','")}')`})
const requestGeoJsonFromAPI = (colourData, apiBase, codeCol, queryParams) => {
    const createFetch = filterParam => fetch(apiBase + new URLSearchParams({...queryParams, ...filterParam}).toString()).then(response => response.json())
    return chunkArr(Object.keys(colourData), 50).map(arrToFilterParam).map(createFetch)
}
const loadShapesToLayer = (colourData, apiBase, codeCol, queryParams, styleFunc, map) => {
    let layer = L.geoJSON(null, {style: styleFunc}).addTo(map)
    requestGeoJsonFromAPI(imd_bham, apiBase, codeCol, queryParams).map(apiRequest => apiRequest.then(geoJson => layer.addData(geoJson)))
    return layer
}
// const concatGeoJSON = geoJsonArr => ({"type" : "FeatureCollection", "features": [].concat(...geoJsonArr.map(geoJson => geoJson.features))})
const styleFuncGenerator = (colourData, colourFunc) => {
    const defaults = {"color": "black", "weight": 0.1}
    return feature => {
        const id = feature.properties[codeCol]
        const val = colourData[id]
        if (val === undefined) return {...defaults, fillColor: "#cccccc", fillOpacity: 1}
        if (Math.abs(val) < 0) return {...defaults, fillColor: "#ffbe33", fillOpacity: 1 / 12}
        return {...defaults, fillColor: colourFunc(val), fillOpacity: 1 / 3}
    }

}

const imd_bham = {"E01008881":2,"E01008882":1,"E01008883":2,"E01008884":2,"E01008885":5,"E01008886":2,"E01008887":1,"E01008888":5,"E01008889":2,"E01008890":3,"E01008891":4,"E01008892":2,"E01008893":3,"E01008894":2,"E01008895":3,"E01008896":1,"E01008897":2,"E01008898":1,"E01008899":1,"E01008901":1,"E01008905":1,"E01008906":1,"E01008907":1,"E01008909":1,"E01008910":1,"E01008911":1,"E01008913":1,"E01008914":1,"E01008915":2,"E01008916":1,"E01008917":5,"E01008918":1,"E01008919":2,"E01008920":4,"E01008921":3,"E01008923":1,"E01008924":3,"E01008925":6,"E01008927":1,"E01008928":1,"E01008929":1,"E01008930":3,"E01008931":1,"E01008932":1,"E01008933":3,"E01008934":6,"E01008935":1,"E01008936":3,"E01008937":2,"E01008938":1,"E01008939":2,"E01008940":1,"E01008941":1,"E01008942":2,"E01008943":2,"E01008944":2,"E01008945":3,"E01008946":2,"E01008947":4,"E01008948":5,"E01008949":7,"E01008950":3,"E01008951":5,"E01008952":3,"E01008953":3,"E01008954":5,"E01008955":4,"E01008956":6,"E01008957":3,"E01008958":2,"E01008959":5,"E01008960":5,"E01008961":4,"E01008962":1,"E01008963":2,"E01008964":2,"E01008965":6,"E01008966":1,"E01008967":7,"E01008968":7,"E01008969":5,"E01008970":3,"E01008971":5,"E01008972":1,"E01008973":4,"E01008974":5,"E01008975":5,"E01008976":1,"E01008977":3,"E01008978":1,"E01008979":1,"E01008980":1,"E01008981":5,"E01008982":4,"E01008984":2,"E01008986":3,"E01008987":2,"E01008988":3,"E01008989":3,"E01008990":9,"E01008991":9,"E01008992":7,"E01008994":5,"E01008995":1,"E01008996":1,"E01008997":4,"E01008998":1,"E01008999":2,"E01009000":1,"E01009001":3,"E01009002":1,"E01009003":3,"E01009005":3,"E01009006":3,"E01009007":1,"E01009008":5,"E01009009":5,"E01009011":4,"E01009012":4,"E01009013":1,"E01009014":2,"E01009015":3,"E01009016":1,"E01009017":2,"E01009018":2,"E01009019":1,"E01009020":1,"E01009021":1,"E01009022":2,"E01009023":5,"E01009024":1,"E01009025":1,"E01009026":1,"E01009028":2,"E01009029":2,"E01009030":4,"E01009031":5,"E01009032":5,"E01009033":1,"E01009034":6,"E01009035":4,"E01009036":6,"E01009037":5,"E01009039":7,"E01009040":7,"E01009041":6,"E01009042":5,"E01009043":2,"E01009044":2,"E01009045":3,"E01009046":5,"E01009047":1,"E01009048":1,"E01009049":3,"E01009050":2,"E01009051":1,"E01009053":1,"E01009054":2,"E01009056":1,"E01009057":1,"E01009058":2,"E01009059":1,"E01009060":1,"E01009061":1,"E01009062":1,"E01009064":2,"E01009065":4,"E01009066":6,"E01009067":8,"E01009068":8,"E01009069":6,"E01009070":7,"E01009071":4,"E01009072":5,"E01009073":1,"E01009074":1,"E01009075":2,"E01009077":3,"E01009078":4,"E01009079":1,"E01009080":1,"E01009081":1,"E01009082":2,"E01009083":1,"E01009084":3,"E01009085":4,"E01009086":3,"E01009087":4,"E01009088":2,"E01009089":4,"E01009090":2,"E01009091":2,"E01009092":1,"E01009093":1,"E01009094":1,"E01009095":3,"E01009096":1,"E01009097":1,"E01009098":2,"E01009099":1,"E01009100":2,"E01009101":2,"E01009102":2,"E01009103":1,"E01009104":1,"E01009105":3,"E01009106":3,"E01009107":1,"E01009108":5,"E01009109":1,"E01009110":1,"E01009111":4,"E01009112":3,"E01009113":1,"E01009114":1,"E01009115":1,"E01009116":7,"E01009117":1,"E01009118":3,"E01009119":4,"E01009120":3,"E01009121":2,"E01009122":1,"E01009123":1,"E01009124":1,"E01009125":1,"E01009126":6,"E01009127":1,"E01009128":1,"E01009129":1,"E01009130":1,"E01009131":1,"E01009132":1,"E01009133":1,"E01009134":1,"E01009135":5,"E01009136":1,"E01009137":1,"E01009138":3,"E01009139":4,"E01009140":3,"E01009141":1,"E01009143":1,"E01009145":3,"E01009146":1,"E01009147":1,"E01009151":2,"E01009152":1,"E01009153":1,"E01009155":1,"E01009157":1,"E01009158":2,"E01009159":5,"E01009160":1,"E01009161":2,"E01009162":4,"E01009163":2,"E01009164":3,"E01009165":2,"E01009166":4,"E01009167":4,"E01009168":5,"E01009169":5,"E01009170":7,"E01009171":2,"E01009172":1,"E01009173":1,"E01009174":1,"E01009175":4,"E01009176":4,"E01009177":5,"E01009178":3,"E01009179":5,"E01009182":1,"E01009183":6,"E01009184":3,"E01009185":5,"E01009186":5,"E01009187":5,"E01009188":4,"E01009189":7,"E01009192":1,"E01009194":1,"E01009195":1,"E01009197":1,"E01009198":1,"E01009199":3,"E01009200":1,"E01009201":1,"E01009202":1,"E01009203":1,"E01009204":1,"E01009205":4,"E01009206":6,"E01009207":6,"E01009208":7,"E01009209":3,"E01009210":2,"E01009211":5,"E01009212":1,"E01009213":2,"E01009214":1,"E01009215":1,"E01009216":3,"E01009217":6,"E01009218":4,"E01009219":3,"E01009220":3,"E01009221":3,"E01009222":1,"E01009223":4,"E01009224":4,"E01009225":2,"E01009226":4,"E01009227":5,"E01009228":4,"E01009229":4,"E01009230":5,"E01009231":4,"E01009232":3,"E01009233":2,"E01009234":5,"E01009235":5,"E01009236":4,"E01009237":3,"E01009238":4,"E01009239":3,"E01009240":5,"E01009241":4,"E01009242":3,"E01009243":4,"E01009244":5,"E01009245":5,"E01009246":5,"E01009247":5,"E01009248":5,"E01009249":4,"E01009250":4,"E01009251":7,"E01009252":8,"E01009253":5,"E01009254":2,"E01009255":3,"E01009256":3,"E01009257":2,"E01009258":1,"E01009259":1,"E01009260":7,"E01009261":6,"E01009262":5,"E01009263":2,"E01009264":3,"E01009265":2,"E01009266":2,"E01009267":5,"E01009268":4,"E01009269":1,"E01009270":1,"E01009271":1,"E01009272":1,"E01009273":1,"E01009274":1,"E01009275":1,"E01009276":4,"E01009278":6,"E01009279":5,"E01009280":5,"E01009281":6,"E01009282":3,"E01009283":5,"E01009284":4,"E01009286":5,"E01009288":5,"E01009289":4,"E01009290":5,"E01009291":2,"E01009292":7,"E01009293":5,"E01009294":3,"E01009295":5,"E01009296":4,"E01009297":1,"E01009298":1,"E01009299":1,"E01009300":1,"E01009301":1,"E01009302":3,"E01009303":1,"E01009304":2,"E01009305":1,"E01009306":1,"E01009307":1,"E01009308":1,"E01009309":1,"E01009310":1,"E01009311":1,"E01009312":5,"E01009313":4,"E01009314":2,"E01009315":3,"E01009316":3,"E01009317":2,"E01009318":7,"E01009319":6,"E01009320":4,"E01009321":1,"E01009322":1,"E01009323":1,"E01009324":5,"E01009325":1,"E01009326":1,"E01009327":1,"E01009328":1,"E01009329":1,"E01009331":1,"E01009332":1,"E01009333":1,"E01009334":1,"E01009335":1,"E01009337":1,"E01009338":1,"E01009339":1,"E01009340":2,"E01009341":1,"E01009342":2,"E01009343":1,"E01009344":1,"E01009345":1,"E01009346":1,"E01009347":1,"E01009348":2,"E01009349":1,"E01009350":1,"E01009351":1,"E01009352":1,"E01009353":1,"E01009354":1,"E01009355":1,"E01009358":1,"E01009359":1,"E01009360":1,"E01009361":1,"E01009362":1,"E01009363":1,"E01009364":1,"E01009365":1,"E01009366":1,"E01009367":1,"E01009368":1,"E01009371":1,"E01009372":1,"E01009373":1,"E01009374":1,"E01009375":1,"E01009376":1,"E01009377":1,"E01009378":1,"E01009379":1,"E01009380":1,"E01009382":1,"E01009383":2,"E01009384":1,"E01009385":2,"E01009389":2,"E01009390":1,"E01009391":2,"E01009392":3,"E01009393":2,"E01009394":4,"E01009395":2,"E01009396":1,"E01009397":1,"E01009399":1,"E01009400":1,"E01009401":1,"E01009403":2,"E01009404":1,"E01009405":2,"E01009406":1,"E01009407":2,"E01009408":1,"E01009409":1,"E01009410":1,"E01009411":3,"E01009412":2,"E01009413":1,"E01009414":2,"E01009415":10,"E01009416":9,"E01009417":7,"E01009418":5,"E01009419":6,"E01009420":9,"E01009421":10,"E01009422":9,"E01009423":4,"E01009424":7,"E01009425":8,"E01009426":10,"E01009427":7,"E01009428":10,"E01009429":10,"E01009430":9,"E01009431":10,"E01009432":5,"E01009433":9,"E01009434":8,"E01009435":9,"E01009436":10,"E01009437":8,"E01009438":9,"E01009439":7,"E01009440":8,"E01009441":3,"E01009442":7,"E01009443":7,"E01009444":10,"E01009445":2,"E01009446":7,"E01009447":5,"E01009448":3,"E01009449":5,"E01009450":7,"E01009451":4,"E01009452":6,"E01009453":7,"E01009454":8,"E01009455":2,"E01009456":9,"E01009457":10,"E01009458":3,"E01009459":9,"E01009460":4,"E01009461":10,"E01009462":6,"E01009463":8,"E01009464":8,"E01009465":8,"E01009466":9,"E01009467":6,"E01009468":8,"E01009469":9,"E01009470":10,"E01009471":8,"E01009472":9,"E01009473":6,"E01009474":7,"E01009475":1,"E01009476":1,"E01009477":1,"E01009478":1,"E01009479":1,"E01009480":1,"E01009481":2,"E01009482":1,"E01009483":1,"E01009484":1,"E01009485":1,"E01009486":1,"E01009487":2,"E01009488":1,"E01009489":1,"E01009490":1,"E01009491":1,"E01009492":1,"E01009493":1,"E01009494":1,"E01009495":2,"E01009496":6,"E01009497":4,"E01009498":1,"E01009499":2,"E01009500":1,"E01009501":1,"E01009502":1,"E01009503":1,"E01009504":5,"E01009505":2,"E01009506":8,"E01009507":1,"E01009508":2,"E01009509":2,"E01009510":1,"E01009511":1,"E01009512":2,"E01009513":1,"E01009514":1,"E01009515":2,"E01009516":2,"E01009517":2,"E01009518":4,"E01009519":5,"E01009520":6,"E01009521":4,"E01009921":4,"E01009922":3,"E01009923":5,"E01009924":6,"E01009925":6,"E01009926":5,"E01009927":4,"E01009928":3,"E01009929":1,"E01009930":3,"E01009931":7,"E01009932":2,"E01009933":2,"E01009934":2,"E01009935":2,"E01009936":5,"E01009937":2,"E01009938":3,"E01009939":5,"E01009940":3,"E01009941":3,"E01009942":2,"E01009943":1,"E01009944":2,"E01009946":5,"E01009947":3,"E01009948":5,"E01009949":8,"E01009950":3,"E01009951":1,"E01009952":1,"E01009953":2,"E01009954":3,"E01009955":2,"E01009956":3,"E01009957":1,"E01009958":8,"E01009959":9,"E01009960":2,"E01009961":6,"E01009962":1,"E01009963":1,"E01009964":1,"E01009965":1,"E01009966":2,"E01009967":3,"E01009968":6,"E01009969":3,"E01009970":4,"E01009971":3,"E01009972":6,"E01009973":5,"E01009974":7,"E01009975":7,"E01009976":6,"E01009977":3,"E01009978":1,"E01009979":1,"E01009980":2,"E01009981":2,"E01009982":2,"E01009983":1,"E01009985":2,"E01009986":2,"E01009987":1,"E01009988":1,"E01009989":3,"E01009991":2,"E01009992":3,"E01009993":1,"E01009994":2,"E01009995":3,"E01009996":1,"E01009997":2,"E01009998":2,"E01009999":2,"E01010000":5,"E01010001":2,"E01010002":4,"E01010003":2,"E01010004":2,"E01010005":3,"E01010006":4,"E01010007":4,"E01010008":5,"E01010009":4,"E01010010":2,"E01010011":6,"E01010012":6,"E01010013":7,"E01010014":5,"E01010015":4,"E01010016":2,"E01010017":2,"E01010018":3,"E01010019":2,"E01010020":2,"E01010021":2,"E01010022":5,"E01010023":6,"E01010024":7,"E01010025":2,"E01010026":5,"E01010027":7,"E01010028":2,"E01010029":1,"E01010030":1,"E01010031":1,"E01010032":1,"E01010033":1,"E01010034":7,"E01010035":6,"E01010036":2,"E01010037":1,"E01010038":2,"E01010039":1,"E01010040":4,"E01010041":2,"E01010042":3,"E01010043":6,"E01010044":3,"E01010045":2,"E01010046":1,"E01010047":2,"E01010048":2,"E01010049":2,"E01010050":3,"E01010051":3,"E01010052":1,"E01010053":1,"E01010054":1,"E01010055":3,"E01010056":2,"E01010057":2,"E01010058":2,"E01010059":2,"E01010060":1,"E01010061":1,"E01010062":1,"E01010063":1,"E01010064":1,"E01010065":2,"E01010066":1,"E01010067":1,"E01010068":2,"E01010069":5,"E01010070":3,"E01010071":2,"E01010072":4,"E01010073":2,"E01010074":2,"E01010075":6,"E01010076":1,"E01010077":2,"E01010078":7,"E01010079":6,"E01010080":1,"E01010081":7,"E01010082":6,"E01010083":3,"E01010084":1,"E01010085":3,"E01010086":2,"E01010087":2,"E01010088":2,"E01010089":3,"E01010090":2,"E01010091":2,"E01010092":3,"E01010093":2,"E01010094":3,"E01010095":1,"E01010096":2,"E01010097":3,"E01010098":1,"E01010099":3,"E01010100":4,"E01010101":2,"E01010102":2,"E01010103":1,"E01010104":2,"E01010105":3,"E01010106":2,"E01010107":1,"E01010108":10,"E01010109":5,"E01010110":5,"E01010111":1,"E01010112":4,"E01010113":3,"E01010114":6,"E01010115":6,"E01010116":9,"E01010117":8,"E01010118":5,"E01010119":8,"E01010120":4,"E01010121":7,"E01010122":7,"E01010123":7,"E01010124":8,"E01010125":1,"E01010126":1,"E01010127":3,"E01010128":2,"E01010129":1,"E01010130":1,"E01010131":1,"E01010132":6,"E01010133":6,"E01010134":8,"E01010135":6,"E01010136":7,"E01010137":3,"E01010138":7,"E01010139":3,"E01010140":1,"E01010141":1,"E01010142":1,"E01010143":1,"E01010144":3,"E01010145":4,"E01010146":2,"E01010147":1,"E01010148":1,"E01010149":4,"E01010150":10,"E01010151":8,"E01010152":10,"E01010153":10,"E01010154":9,"E01010155":10,"E01010156":10,"E01010157":7,"E01010158":2,"E01010159":5,"E01010160":5,"E01010161":8,"E01010162":8,"E01010163":7,"E01010164":7,"E01010165":5,"E01010166":9,"E01010167":6,"E01010168":9,"E01010169":10,"E01010170":10,"E01010171":8,"E01010172":10,"E01010173":10,"E01010174":6,"E01010175":9,"E01010176":10,"E01010177":6,"E01010178":3,"E01010179":8,"E01010180":10,"E01010181":10,"E01010183":10,"E01010184":7,"E01010185":10,"E01010186":10,"E01010187":10,"E01010188":10,"E01010189":10,"E01010190":10,"E01010191":10,"E01010192":8,"E01010193":10,"E01010194":10,"E01010195":10,"E01010196":10,"E01010197":10,"E01010198":10,"E01010199":10,"E01010200":6,"E01010201":8,"E01010202":10,"E01010203":8,"E01010204":2,"E01010205":10,"E01010206":9,"E01010207":10,"E01010208":9,"E01010209":8,"E01010210":10,"E01010211":6,"E01010212":10,"E01010213":5,"E01010214":10,"E01010215":9,"E01010216":10,"E01010217":10,"E01010218":3,"E01010219":7,"E01010220":9,"E01010221":6,"E01010222":9,"E01010223":6,"E01010225":9,"E01010226":8,"E01010227":10,"E01010228":7,"E01010229":10,"E01010230":6,"E01010231":10,"E01010232":6,"E01010233":6,"E01010234":1,"E01010235":1,"E01010236":1,"E01010237":3,"E01010238":1,"E01010239":2,"E01010240":2,"E01010241":8,"E01010242":3,"E01010243":7,"E01010244":3,"E01010245":8,"E01010246":7,"E01010247":7,"E01010248":10,"E01010249":3,"E01010250":5,"E01010251":10,"E01010252":4,"E01010253":4,"E01010254":4,"E01010255":9,"E01010256":5,"E01010257":10,"E01010258":2,"E01010259":4,"E01010260":2,"E01010261":2,"E01010262":3,"E01010263":2,"E01010264":2,"E01010265":2,"E01010266":2,"E01010267":5,"E01010268":2,"E01010269":1,"E01010270":2,"E01010271":1,"E01010272":1,"E01010273":1,"E01010274":1,"E01010275":1,"E01010277":2,"E01010279":2,"E01010282":1,"E01010283":1,"E01010284":2,"E01010285":5,"E01010286":1,"E01010287":2,"E01010288":1,"E01010289":1,"E01010290":3,"E01010291":1,"E01010292":1,"E01010293":2,"E01010294":1,"E01010295":1,"E01010296":10,"E01010297":10,"E01010298":4,"E01010299":2,"E01010300":2,"E01010301":2,"E01010302":2,"E01010303":4,"E01010304":4,"E01010305":2,"E01010306":5,"E01010307":8,"E01010308":1,"E01010309":2,"E01010310":2,"E01010311":2,"E01010312":2,"E01010313":2,"E01010314":2,"E01010315":2,"E01010316":1,"E01010317":7,"E01010318":1,"E01010319":9,"E01010320":3,"E01010321":3,"E01010322":4,"E01010323":4,"E01010324":4,"E01010325":4,"E01010326":6,"E01010327":3,"E01010328":9,"E01010329":8,"E01010330":4,"E01010331":9,"E01010332":9,"E01010333":8,"E01010334":9,"E01010335":2,"E01010336":3,"E01010337":5,"E01010338":2,"E01010339":6,"E01010340":1,"E01010341":2,"E01010342":1,"E01010343":2,"E01010344":2,"E01010345":7,"E01010346":9,"E01010347":2,"E01010348":5,"E01010349":4,"E01010350":6,"E01010351":5,"E01010352":8,"E01010353":4,"E01010354":5,"E01010355":7,"E01010356":7,"E01010357":8,"E01010358":6,"E01010359":7,"E01010360":8,"E01010361":4,"E01010362":2,"E01010363":2,"E01010364":1,"E01010365":1,"E01010366":1,"E01010367":1,"E01010368":1,"E01010369":1,"E01010370":1,"E01010371":1,"E01010372":2,"E01010373":8,"E01010374":1,"E01010375":1,"E01010376":6,"E01010377":4,"E01010378":5,"E01010379":6,"E01010380":6,"E01010381":3,"E01010382":3,"E01010383":1,"E01010384":10,"E01010385":10,"E01010386":10,"E01010387":10,"E01010388":10,"E01010389":8,"E01010390":9,"E01010391":10,"E01010392":10,"E01010393":5,"E01010394":7,"E01010395":8,"E01010396":3,"E01010397":2,"E01010398":9,"E01010399":5,"E01010400":2,"E01010401":1,"E01010402":5,"E01010403":2,"E01010404":2,"E01010405":2,"E01010406":2,"E01010407":3,"E01010408":2,"E01010409":2,"E01029475":8,"E01029476":8,"E01029477":10,"E01029478":9,"E01029479":9,"E01029480":7,"E01029481":6,"E01029482":6,"E01029483":10,"E01029484":7,"E01029485":10,"E01029486":8,"E01029487":3,"E01029488":6,"E01029489":8,"E01029490":7,"E01029491":7,"E01029492":2,"E01029493":8,"E01029494":6,"E01029495":9,"E01029496":2,"E01029497":6,"E01029498":7,"E01029499":3,"E01029500":8,"E01029501":4,"E01029502":4,"E01029503":5,"E01029504":5,"E01029505":7,"E01029506":9,"E01029507":10,"E01029508":9,"E01029509":8,"E01029511":10,"E01029512":9,"E01029513":10,"E01029514":10,"E01029515":8,"E01029516":6,"E01029517":8,"E01029518":9,"E01029519":7,"E01029520":10,"E01029521":9,"E01029522":6,"E01029523":9,"E01029524":6,"E01029525":8,"E01029526":4,"E01029527":3,"E01029528":4,"E01029529":6,"E01029530":7,"E01029531":10,"E01032122":7,"E01032123":7,"E01032124":7,"E01032125":9,"E01032126":8,"E01032127":8,"E01032128":6,"E01032129":6,"E01032130":7,"E01032131":3,"E01032132":4,"E01032133":5,"E01032134":6,"E01032135":10,"E01032136":7,"E01032137":10,"E01032138":10,"E01032139":10,"E01032140":10,"E01032141":9,"E01032142":9,"E01032143":9,"E01032144":10,"E01032145":10,"E01032146":8,"E01032147":7,"E01032148":10,"E01032149":10,"E01032150":9,"E01032151":10,"E01032152":4,"E01032153":8,"E01032154":10,"E01032155":10,"E01032156":5,"E01032157":4,"E01032158":10,"E01032159":6,"E01032160":8,"E01032161":2,"E01032162":10,"E01032166":6,"E01032168":8,"E01032169":5,"E01032170":7,"E01032171":8,"E01032172":6,"E01032173":9,"E01032174":6,"E01032175":8,"E01032176":8,"E01032177":9,"E01032178":9,"E01032589":5,"E01032590":7,"E01032591":6,"E01032592":5,"E01032885":9,"E01032886":10,"E01032887":1,"E01032888":1,"E01032889":1,"E01032899":6,"E01032900":8,"E01033059":10,"E01033060":4,"E01033061":10,"E01033062":10,"E01033243":7,"E01033557":3,"E01033559":4,"E01033561":3,"E01033562":3,"E01033564":3,"E01033565":3,"E01033567":3,"E01033615":3,"E01033616":1,"E01033617":4,"E01033618":6,"E01033619":5,"E01033620":3,"E01033621":1,"E01033622":4,"E01033623":2,"E01033624":2,"E01033625":4,"E01033626":3,"E01033627":2,"E01033628":1,"E01033629":2,"E01033630":2,"E01033631":7,"E01033632":1,"E01033633":1,"E01033634":4,"E01033635":2,"E01033636":1,"E01033637":1,"E01033638":1,"E01033639":1,"E01033640":1,"E01033641":2,"E01033642":1,"E01033643":1,"E01033644":1,"E01033645":1,"E01033646":1,"E01033647":1,"E01033648":1,"E01033649":1,"E01033650":1}
// const apiBase = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Lower_Layer_Super_Output_Areas_December_2011_Boundaries_EW_BFC_V2/FeatureServer/0/query?"
const apiBase = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Lower_Layer_Super_Output_Areas_DEC_2011_EW_BSC_V3/FeatureServer/0/query?"
const codeCol = "LSOA11CD"
const queryParams = {outFields: "LSOA11CD,LSOA11NM", outSR: "4326", f: "geojson", geometryPrecision: "5"}  // https://developers.arcgis.com/rest/services-reference/query-feature-service-layer-.htm#GUID-62EE7495-8688-4BD0-B433-89F7E4476673
const valToColour = val => color_map_d80f4596e4a049bca6cee55824dd4129.color(val - 1)

const scale = ['#d01c8b', '#f1b6da', '#b8e186', '#4dac26']
const limits = chroma.limits(Object.values(imd_bham), "q", scale.length- 1)
const colours = chroma.scale(scale).colors(limits.length)
const colMap = val => {for (let i = 0; i < limits.length; i++) if (limits[i] >= val) return colours[i]}

let bhamLayer = loadShapesToLayer(imd_bham, apiBase, codeCol, queryParams, styleFuncGenerator(imd_bham, colMap), map_2ea91b0b3ba84b51bd12b87c02a38314)
