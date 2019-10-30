<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology|Labeling" labelsEnabled="1" version="3.4.11-Madeira">
  <renderer-v2 symbollevels="0" forceraster="0" type="categorizedSymbol" attr="nutzerdefiniert" enableorderby="0">
    <categories>
      <category symbol="0" label="Zentren" value="1" render="true"/>
    </categories>
    <symbols>
      <symbol alpha="1" clip_to_extent="1" force_rhr="0" name="0" type="fill">
        <layer locked="0" class="SimpleFill" pass="0" enabled="1">
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="137,207,230,128" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="76,164,191,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0.6" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="solid" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <source-symbol>
      <symbol alpha="1" clip_to_extent="1" force_rhr="0" name="0" type="fill">
        <layer locked="0" class="SimpleFill" pass="0" enabled="1">
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="190,178,151,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0.26" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="solid" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </source-symbol>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <labeling type="simple">
    <settings>
      <text-style fontSizeUnit="Point" fontCapitals="0" fontUnderline="0" fontFamily="MS Shell Dlg 2" fontWordSpacing="0" textColor="0,0,0,255" isExpression="1" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontItalic="0" fieldName="IF (&quot;name&quot; != 'unbekanntes Zentrum' AND &quot;nutzerdefiniert&quot; = 1, &quot;name&quot;, NULL)" useSubstitutions="0" previewBkgrdColor="#ffffff" fontLetterSpacing="0" textOpacity="1" fontWeight="50" fontSize="9" multilineHeight="1" blendMode="0" fontStrikeout="0" namedStyle="Standard">
        <text-buffer bufferOpacity="1" bufferSize="0.8" bufferBlendMode="0" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferColor="255,255,255,255" bufferNoFill="1" bufferDraw="1" bufferSizeUnits="MM" bufferJoinStyle="128"/>
        <background shapeType="0" shapeBorderWidth="0" shapeJoinStyle="64" shapeDraw="0" shapeOpacity="1" shapeRotationType="0" shapeSizeUnit="MM" shapeFillColor="255,255,255,255" shapeRadiiUnit="MM" shapeBorderColor="128,128,128,255" shapeSizeX="0" shapeSizeY="0" shapeOffsetUnit="MM" shapeBlendMode="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeBorderWidthUnit="MM" shapeRotation="0" shapeSizeType="0" shapeSVGFile="" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiY="0" shapeRadiiX="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetY="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetX="0"/>
        <shadow shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetUnit="MM" shadowDraw="0" shadowOffsetAngle="135" shadowOpacity="0.7" shadowRadiusAlphaOnly="0" shadowRadiusUnit="MM" shadowColor="0,0,0,255" shadowBlendMode="6" shadowUnder="0" shadowOffsetGlobal="1" shadowRadius="1.5" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowScale="100" shadowOffsetDist="1"/>
        <substitutions/>
      </text-style>
      <text-format reverseDirectionSymbol="0" leftDirectionSymbol="&lt;" plussign="0" wrapChar="" placeDirectionSymbol="0" rightDirectionSymbol=">" useMaxLineLengthForAutoWrap="1" autoWrapLength="0" decimals="3" multilineAlign="4294967295" addDirectionSymbol="0" formatNumbers="0"/>
      <placement offsetType="0" placement="1" maxCurvedCharAngleOut="-25" dist="0" distMapUnitScale="3x:0,0,0,0,0,0" repeatDistance="0" repeatDistanceUnits="MM" fitInPolygonOnly="0" centroidInside="0" priority="5" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" yOffset="0" xOffset="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" quadOffset="4" distUnits="MM" maxCurvedCharAngleIn="25" centroidWhole="0" preserveRotation="1" offsetUnits="MM" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" rotationAngle="0" placementFlags="10"/>
      <rendering displayAll="0" obstacleFactor="1" fontMaxPixelSize="10000" maxNumLabels="2000" scaleMin="0" obstacle="1" upsidedownLabels="0" labelPerPart="0" zIndex="0" mergeLines="0" obstacleType="0" scaleMax="0" drawLabels="1" fontMinPixelSize="3" scaleVisibility="0" limitNumLabels="0" fontLimitPixelSize="0" minFeatureSize="0"/>
      <dd_properties>
        <Option type="Map">
          <Option value="" name="name" type="QString"/>
          <Option name="properties"/>
          <Option value="collection" name="type" type="QString"/>
        </Option>
      </dd_properties>
    </settings>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerGeometryType>2</layerGeometryType>
</qgis>
