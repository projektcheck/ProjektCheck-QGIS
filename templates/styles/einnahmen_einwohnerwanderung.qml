<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology|Labeling" labelsEnabled="1" version="3.10.3-A Coruña">
  <renderer-v2 type="singleSymbol" forceraster="0" symbollevels="0" enableorderby="0">
    <symbols>
      <symbol force_rhr="0" type="fill" name="0" alpha="1" clip_to_extent="1">
        <layer pass="0" class="SimpleFill" enabled="1" locked="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="35,139,69,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="76,76,76,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.2"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" name="name" value=""/>
              <Option type="Map" name="properties">
                <Option type="Map" name="fillColor">
                  <Option type="bool" name="active" value="true"/>
                  <Option type="QString" name="expression" value="coalesce(ramp_color(create_ramp(map(0,'#67000d',0.13,'#a50f15',0.26,'#cb181d',0.39,'#ef3b2c',0.52,'#fb6a4a',0.65,'#fc9272',0.78,'#fcbba1',0.9,'#fee0d2',1,'#fff5f0')),scale_linear(IF (&quot;saldo&quot; > 0, NULL, &quot;saldo&quot;), minimum(&quot;saldo&quot;), 0, 0, 1)), '#238b45')"/>
                  <Option type="int" name="type" value="3"/>
                </Option>
              </Option>
              <Option type="QString" name="type" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style namedStyle="Standard" fontItalic="0" fontCapitals="0" fontSizeUnit="Point" blendMode="0" textColor="0,0,0,255" fontWordSpacing="0" fontLetterSpacing="0" previewBkgrdColor="255,255,255,255" fontSize="8" textOpacity="1" multilineHeight="1" fontKerning="1" isExpression="1" useSubstitutions="0" textOrientation="horizontal" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontWeight="50" fontUnderline="0" fontStrikeout="0" fieldName=" IF (round( &quot;saldo&quot;, 1) = 0, &quot;GEN&quot; || '\\' ||'±' || round( &quot;saldo&quot;, 1) || ' Ew', &#xd;&#xa;&#x9;IF (round( &quot;saldo&quot;, 1) > 0, &quot;GEN&quot; || '\\' ||'+' || round( &quot;saldo&quot;, 1) || ' Ew', &#xd;&#xa;&#x9;&#x9;&quot;GEN&quot; || '\\' ||round( &quot;saldo&quot;, 1) || ' Ew'))" fontFamily="MS Shell Dlg 2">
        <text-buffer bufferSizeUnits="MM" bufferNoFill="1" bufferOpacity="1" bufferSize="0" bufferJoinStyle="128" bufferColor="255,255,255,255" bufferBlendMode="0" bufferDraw="1" bufferSizeMapUnitScale="3x:0,0,0,0,0,0"/>
        <background shapeRadiiX="0" shapeSizeY="0" shapeOffsetUnit="MM" shapeRadiiUnit="MM" shapeRotation="0" shapeFillColor="255,255,255,255" shapeSizeX="0" shapeType="0" shapeBorderColor="128,128,128,255" shapeBorderWidth="0" shapeSizeUnit="MM" shapeOffsetY="0" shapeBorderWidthUnit="MM" shapeJoinStyle="64" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeSVGFile="" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetX="0" shapeRadiiY="0" shapeBlendMode="0" shapeSizeType="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeDraw="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeOpacity="1" shapeRotationType="0">
          <symbol force_rhr="0" type="marker" name="markerSymbol" alpha="1" clip_to_extent="1">
            <layer pass="0" class="SimpleMarker" enabled="1" locked="0">
              <prop k="angle" v="0"/>
              <prop k="color" v="243,166,178,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="35,35,35,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="diameter"/>
              <prop k="size" v="2"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" name="name" value=""/>
                  <Option name="properties"/>
                  <Option type="QString" name="type" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowRadiusAlphaOnly="0" shadowOffsetGlobal="1" shadowRadiusUnit="MM" shadowDraw="0" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetDist="1" shadowBlendMode="6" shadowOffsetUnit="MM" shadowOpacity="0" shadowColor="0,0,0,255" shadowScale="100" shadowUnder="0" shadowOffsetAngle="135" shadowRadius="0"/>
        <dd_properties>
          <Option type="Map">
            <Option type="QString" name="name" value=""/>
            <Option name="properties"/>
            <Option type="QString" name="type" value="collection"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format leftDirectionSymbol="&lt;" reverseDirectionSymbol="0" decimals="3" useMaxLineLengthForAutoWrap="1" plussign="0" formatNumbers="0" multilineAlign="1" rightDirectionSymbol=">" placeDirectionSymbol="0" autoWrapLength="0" addDirectionSymbol="0" wrapChar="\"/>
      <placement maxCurvedCharAngleIn="25" placement="1" placementFlags="10" geometryGeneratorEnabled="0" yOffset="0" quadOffset="4" repeatDistanceUnits="MM" overrunDistance="0" overrunDistanceUnit="MM" distUnits="MM" rotationAngle="0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" distMapUnitScale="3x:0,0,0,0,0,0" offsetUnits="MM" dist="0" maxCurvedCharAngleOut="-25" layerType="PolygonGeometry" fitInPolygonOnly="0" geometryGenerator="" centroidInside="0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" xOffset="0" priority="5" repeatDistance="0" preserveRotation="1" centroidWhole="0" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" geometryGeneratorType="PointGeometry" offsetType="0"/>
      <rendering fontMaxPixelSize="10000" drawLabels="1" displayAll="0" scaleMin="0" maxNumLabels="2000" obstacleType="0" scaleMax="0" upsidedownLabels="0" limitNumLabels="0" mergeLines="0" obstacle="1" labelPerPart="0" fontMinPixelSize="3" fontLimitPixelSize="0" scaleVisibility="0" zIndex="0" obstacleFactor="1" minFeatureSize="0"/>
      <dd_properties>
        <Option type="Map">
          <Option type="QString" name="name" value=""/>
          <Option type="Map" name="properties">
            <Option type="Map" name="BufferSize">
              <Option type="bool" name="active" value="true"/>
              <Option type="QString" name="expression" value="0.75"/>
              <Option type="int" name="type" value="3"/>
            </Option>
          </Option>
          <Option type="QString" name="type" value="collection"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option type="QString" name="anchorPoint" value="pole_of_inaccessibility"/>
          <Option type="Map" name="ddProperties">
            <Option type="QString" name="name" value=""/>
            <Option name="properties"/>
            <Option type="QString" name="type" value="collection"/>
          </Option>
          <Option type="bool" name="drawToAllParts" value="false"/>
          <Option type="QString" name="enabled" value="0"/>
          <Option type="QString" name="lineSymbol" value="&lt;symbol force_rhr=&quot;0&quot; type=&quot;line&quot; name=&quot;symbol&quot; alpha=&quot;1&quot; clip_to_extent=&quot;1&quot;>&lt;layer pass=&quot;0&quot; class=&quot;SimpleLine&quot; enabled=&quot;1&quot; locked=&quot;0&quot;>&lt;prop k=&quot;capstyle&quot; v=&quot;square&quot;/>&lt;prop k=&quot;customdash&quot; v=&quot;5;2&quot;/>&lt;prop k=&quot;customdash_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;customdash_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;draw_inside_polygon&quot; v=&quot;0&quot;/>&lt;prop k=&quot;joinstyle&quot; v=&quot;bevel&quot;/>&lt;prop k=&quot;line_color&quot; v=&quot;60,60,60,255&quot;/>&lt;prop k=&quot;line_style&quot; v=&quot;solid&quot;/>&lt;prop k=&quot;line_width&quot; v=&quot;0.3&quot;/>&lt;prop k=&quot;line_width_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;offset&quot; v=&quot;0&quot;/>&lt;prop k=&quot;offset_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;offset_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;ring_filter&quot; v=&quot;0&quot;/>&lt;prop k=&quot;use_custom_dash&quot; v=&quot;0&quot;/>&lt;prop k=&quot;width_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; name=&quot;name&quot; value=&quot;&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option type=&quot;QString&quot; name=&quot;type&quot; value=&quot;collection&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>"/>
          <Option type="double" name="minLength" value="0"/>
          <Option type="QString" name="minLengthMapUnitScale" value="3x:0,0,0,0,0,0"/>
          <Option type="QString" name="minLengthUnit" value="MM"/>
          <Option type="double" name="offsetFromAnchor" value="0"/>
          <Option type="QString" name="offsetFromAnchorMapUnitScale" value="3x:0,0,0,0,0,0"/>
          <Option type="QString" name="offsetFromAnchorUnit" value="MM"/>
          <Option type="double" name="offsetFromLabel" value="0"/>
          <Option type="QString" name="offsetFromLabelMapUnitScale" value="3x:0,0,0,0,0,0"/>
          <Option type="QString" name="offsetFromLabelUnit" value="MM"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerGeometryType>2</layerGeometryType>
</qgis>
