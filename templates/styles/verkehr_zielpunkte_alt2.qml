<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis labelsEnabled="1" version="3.4.11-Madeira" styleCategories="Symbology|Labeling">
  <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0">
    <symbols>
      <symbol force_rhr="0" alpha="1" type="marker" name="0" clip_to_extent="1">
        <layer pass="0" locked="0" class="SimpleMarker" enabled="1">
          <prop v="0" k="angle"/>
          <prop v="20,204,204,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="77,77,77,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="scale_linear(  &quot;weight&quot; , 0,100,1,8)" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <labeling type="simple">
    <settings>
      <text-style fontWeight="50" previewBkgrdColor="#ffffff" fontItalic="0" fontUnderline="0" textOpacity="1" fieldName="&quot;name&quot; || '\\' ||   round( &quot;weight&quot; , 0) || ' % Gewichtung'" fontSizeUnit="Point" fontFamily="MS Shell Dlg 2" blendMode="0" multilineHeight="1" fontCapitals="0" fontSize="8" useSubstitutions="0" fontLetterSpacing="0" isExpression="1" namedStyle="Standard" fontWordSpacing="0" textColor="0,0,0,255" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontStrikeout="0">
        <text-buffer bufferColor="255,255,255,255" bufferOpacity="1" bufferSize="0,8" bufferNoFill="1" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferBlendMode="0" bufferSizeUnits="MM" bufferDraw="1" bufferJoinStyle="128"/>
        <background shapeJoinStyle="64" shapeSizeY="0" shapeType="0" shapeRotation="0" shapeOpacity="1" shapeRadiiUnit="MM" shapeBorderColor="128,128,128,255" shapeSizeUnit="MM" shapeFillColor="255,255,255,255" shapeRadiiX="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeBorderWidth="0" shapeOffsetX="0" shapeOffsetY="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeSizeX="0" shapeBorderWidthUnit="MM" shapeSizeType="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiY="0" shapeRotationType="0" shapeSVGFile="" shapeBlendMode="0" shapeOffsetUnit="MM" shapeDraw="0"/>
        <shadow shadowOffsetAngle="135" shadowBlendMode="6" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetUnit="MM" shadowDraw="0" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowScale="100" shadowColor="0,0,0,255" shadowOpacity="0" shadowOffsetGlobal="1" shadowUnder="0" shadowOffsetDist="1" shadowRadiusAlphaOnly="0" shadowRadius="0" shadowRadiusUnit="MM"/>
        <substitutions/>
      </text-style>
      <text-format decimals="3" addDirectionSymbol="0" placeDirectionSymbol="0" leftDirectionSymbol="&lt;" reverseDirectionSymbol="0" formatNumbers="0" useMaxLineLengthForAutoWrap="1" wrapChar="\" autoWrapLength="0" multilineAlign="3" rightDirectionSymbol=">" plussign="0"/>
      <placement rotationAngle="0" maxCurvedCharAngleIn="25" distUnits="MM" placement="6" maxCurvedCharAngleOut="-25" offsetUnits="MM" dist="0" centroidInside="0" preserveRotation="1" repeatDistanceUnits="MM" repeatDistance="0" xOffset="0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" quadOffset="4" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" yOffset="0" distMapUnitScale="3x:0,0,0,0,0,0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" priority="5" offsetType="1" placementFlags="10" fitInPolygonOnly="0" centroidWhole="0"/>
      <rendering obstacleFactor="1" maxNumLabels="2000" fontMinPixelSize="3" scaleMin="0" scaleMax="0" scaleVisibility="0" obstacleType="0" zIndex="0" upsidedownLabels="0" fontLimitPixelSize="0" minFeatureSize="0" drawLabels="1" fontMaxPixelSize="10000" displayAll="0" labelPerPart="0" obstacle="1" limitNumLabels="0" mergeLines="0"/>
      <dd_properties>
        <Option type="Map">
          <Option type="QString" value="" name="name"/>
          <Option type="Map" name="properties">
            <Option type="Map" name="BufferSize">
              <Option type="bool" value="true" name="active"/>
              <Option type="QString" value="0.8" name="expression"/>
              <Option type="int" value="3" name="type"/>
            </Option>
          </Option>
          <Option type="QString" value="collection" name="type"/>
        </Option>
      </dd_properties>
    </settings>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerGeometryType>0</layerGeometryType>
</qgis>
