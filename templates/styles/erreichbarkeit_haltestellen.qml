<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology|Labeling" labelsEnabled="1" version="3.4.11-Madeira">
  <renderer-v2 type="singleSymbol" symbollevels="0" forceraster="0" enableorderby="0">
    <symbols>
      <symbol type="marker" force_rhr="0" name="0" alpha="1" clip_to_extent="1">
        <layer class="SimpleMarker" enabled="1" locked="0" pass="0">
          <prop v="0" k="angle"/>
          <prop v="153,153,0,255" k="color"/>
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
          <prop v="2" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="true" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
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
      <text-style fieldName="IF (&quot;abfahrten&quot; > 0, &quot;name&quot; || ' (' || &quot;abfahrten&quot; || ' Abfahrten pro Tag', NULL)" namedStyle="Standard" isExpression="1" fontCapitals="0" fontUnderline="0" previewBkgrdColor="#ffffff" blendMode="0" textColor="77,77,0,255" fontWordSpacing="0" fontFamily="MS Shell Dlg 2" fontLetterSpacing="0" multilineHeight="1" useSubstitutions="0" fontStrikeout="0" fontWeight="50" fontSize="10" fontItalic="0" textOpacity="1" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontSizeUnit="Point">
        <text-buffer bufferDraw="1" bufferSizeUnits="MM" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferColor="255,255,255,255" bufferNoFill="1" bufferOpacity="1" bufferJoinStyle="128" bufferSize="0.9" bufferBlendMode="0"/>
        <background shapeBorderColor="128,128,128,255" shapeSizeUnit="MM" shapeRotation="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeSizeX="0" shapeRadiiX="0" shapeOffsetUnit="MM" shapeJoinStyle="64" shapeType="0" shapeRadiiY="0" shapeSizeY="0" shapeSVGFile="" shapeSizeType="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeDraw="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetX="0" shapeBorderWidth="0" shapeOffsetY="0" shapeRadiiUnit="MM" shapeBorderWidthUnit="MM" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeOpacity="1" shapeRotationType="0" shapeFillColor="255,255,255,255" shapeBlendMode="0"/>
        <shadow shadowRadiusUnit="MM" shadowOffsetGlobal="1" shadowRadiusAlphaOnly="0" shadowDraw="0" shadowOpacity="0.7" shadowColor="0,0,0,255" shadowUnder="0" shadowRadius="1.5" shadowBlendMode="6" shadowOffsetAngle="135" shadowOffsetUnit="MM" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetDist="1" shadowScale="100" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0"/>
        <substitutions/>
      </text-style>
      <text-format formatNumbers="0" placeDirectionSymbol="0" decimals="3" wrapChar="" multilineAlign="3" useMaxLineLengthForAutoWrap="1" rightDirectionSymbol=">" plussign="0" leftDirectionSymbol="&lt;" autoWrapLength="0" addDirectionSymbol="0" reverseDirectionSymbol="0"/>
      <placement priority="5" repeatDistanceUnits="MM" yOffset="0" rotationAngle="0" repeatDistance="0" fitInPolygonOnly="0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" distUnits="MM" placement="6" centroidInside="0" dist="0" quadOffset="4" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" offsetType="1" placementFlags="10" distMapUnitScale="3x:0,0,0,0,0,0" maxCurvedCharAngleIn="25" offsetUnits="MM" xOffset="0" preserveRotation="1" centroidWhole="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" maxCurvedCharAngleOut="-25"/>
      <rendering maxNumLabels="2000" scaleMax="0" minFeatureSize="0" obstacle="1" obstacleType="0" labelPerPart="0" obstacleFactor="1" mergeLines="0" fontMinPixelSize="3" drawLabels="1" limitNumLabels="0" zIndex="0" fontLimitPixelSize="0" scaleMin="0" fontMaxPixelSize="10000" upsidedownLabels="0" displayAll="0" scaleVisibility="0"/>
      <dd_properties>
        <Option type="Map">
          <Option value="" type="QString" name="name"/>
          <Option name="properties"/>
          <Option value="collection" type="QString" name="type"/>
        </Option>
      </dd_properties>
    </settings>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerGeometryType>0</layerGeometryType>
</qgis>
