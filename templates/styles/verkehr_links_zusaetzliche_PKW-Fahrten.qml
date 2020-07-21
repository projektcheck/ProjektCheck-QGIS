<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.10.3-A Coruña" labelsEnabled="1" styleCategories="Symbology|Labeling">
  <renderer-v2 symbollevels="0" type="singleSymbol" enableorderby="0" forceraster="0">
    <symbols>
      <symbol alpha="1" type="line" name="0" force_rhr="0" clip_to_extent="1">
        <layer class="SimpleLine" enabled="1" locked="0" pass="0">
          <prop k="capstyle" v="flat"/>
          <prop k="customdash" v="5;2"/>
          <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="customdash_unit" v="MM"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="miter"/>
          <prop k="line_color" v="0,0,0,255"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="0.6"/>
          <prop k="line_width_unit" v="MM"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="ring_filter" v="0"/>
          <prop k="use_custom_dash" v="0"/>
          <prop k="width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" name="name" value=""/>
              <Option type="Map" name="properties">
                <Option type="Map" name="outlineWidth">
                  <Option type="bool" name="active" value="true"/>
                  <Option type="QString" name="expression" value="scale_linear(  &quot;trips&quot; , 0, maximum( &quot;trips&quot;),0.2,8)"/>
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
      <text-style fieldName="round( &quot;trips&quot;)" fontWeight="50" fontLetterSpacing="0" fontItalic="0" fontFamily="MS Shell Dlg 2" fontKerning="1" fontUnderline="0" previewBkgrdColor="255,255,255,255" fontSize="10" multilineHeight="1" textOrientation="horizontal" textOpacity="1" isExpression="1" textColor="0,0,0,255" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontCapitals="0" fontSizeUnit="Point" fontStrikeout="0" fontWordSpacing="0" namedStyle="Standard" blendMode="0" useSubstitutions="0">
        <text-buffer bufferSizeUnits="MM" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferOpacity="1" bufferDraw="1" bufferJoinStyle="128" bufferSize="1" bufferColor="255,255,255,255" bufferBlendMode="0" bufferNoFill="1"/>
        <background shapeSizeType="0" shapeSizeUnit="MM" shapeSVGFile="" shapeOffsetUnit="MM" shapeBorderColor="128,128,128,255" shapeJoinStyle="64" shapeRadiiUnit="MM" shapeType="0" shapeRadiiX="0" shapeOffsetX="0" shapeBlendMode="0" shapeRadiiY="0" shapeOffsetY="0" shapeDraw="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeFillColor="255,255,255,255" shapeRotation="0" shapeBorderWidthUnit="MM" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeSizeY="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeSizeX="0" shapeOpacity="1" shapeBorderWidth="0" shapeRotationType="0">
          <symbol alpha="1" type="marker" name="markerSymbol" force_rhr="0" clip_to_extent="1">
            <layer class="SimpleMarker" enabled="1" locked="0" pass="0">
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
        <shadow shadowOffsetDist="1" shadowOffsetGlobal="1" shadowColor="0,0,0,255" shadowOffsetUnit="MM" shadowRadiusUnit="MM" shadowRadiusAlphaOnly="0" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetAngle="135" shadowDraw="0" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowUnder="0" shadowScale="100" shadowRadius="0" shadowOpacity="0" shadowBlendMode="6"/>
        <dd_properties>
          <Option type="Map">
            <Option type="QString" name="name" value=""/>
            <Option name="properties"/>
            <Option type="QString" name="type" value="collection"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format useMaxLineLengthForAutoWrap="1" reverseDirectionSymbol="0" autoWrapLength="0" wrapChar="" plussign="0" placeDirectionSymbol="0" decimals="3" multilineAlign="4294967295" addDirectionSymbol="0" leftDirectionSymbol="&lt;" rightDirectionSymbol=">" formatNumbers="0"/>
      <placement geometryGeneratorEnabled="0" geometryGeneratorType="PointGeometry" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" distUnits="MM" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" maxCurvedCharAngleIn="60" repeatDistanceUnits="MM" geometryGenerator="" quadOffset="4" distMapUnitScale="3x:0,0,0,0,0,0" centroidWhole="0" fitInPolygonOnly="0" layerType="LineGeometry" rotationAngle="0" yOffset="0" repeatDistance="0" placement="2" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" offsetType="0" priority="5" overrunDistanceUnit="MM" centroidInside="0" preserveRotation="1" offsetUnits="MM" overrunDistance="0" placementFlags="9" dist="0" maxCurvedCharAngleOut="-95" xOffset="0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0"/>
      <rendering labelPerPart="0" displayAll="0" fontMaxPixelSize="10000" mergeLines="1" obstacleFactor="1" obstacleType="0" scaleMin="0" obstacle="1" maxNumLabels="2000" drawLabels="1" scaleVisibility="0" fontLimitPixelSize="0" scaleMax="0" limitNumLabels="1" upsidedownLabels="0" minFeatureSize="0" zIndex="0" fontMinPixelSize="3"/>
      <dd_properties>
        <Option type="Map">
          <Option type="QString" name="name" value=""/>
          <Option name="properties"/>
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
          <Option type="QString" name="lineSymbol" value="&lt;symbol alpha=&quot;1&quot; type=&quot;line&quot; name=&quot;symbol&quot; force_rhr=&quot;0&quot; clip_to_extent=&quot;1&quot;>&lt;layer class=&quot;SimpleLine&quot; enabled=&quot;1&quot; locked=&quot;0&quot; pass=&quot;0&quot;>&lt;prop k=&quot;capstyle&quot; v=&quot;square&quot;/>&lt;prop k=&quot;customdash&quot; v=&quot;5;2&quot;/>&lt;prop k=&quot;customdash_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;customdash_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;draw_inside_polygon&quot; v=&quot;0&quot;/>&lt;prop k=&quot;joinstyle&quot; v=&quot;bevel&quot;/>&lt;prop k=&quot;line_color&quot; v=&quot;60,60,60,255&quot;/>&lt;prop k=&quot;line_style&quot; v=&quot;solid&quot;/>&lt;prop k=&quot;line_width&quot; v=&quot;0.3&quot;/>&lt;prop k=&quot;line_width_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;offset&quot; v=&quot;0&quot;/>&lt;prop k=&quot;offset_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;offset_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;ring_filter&quot; v=&quot;0&quot;/>&lt;prop k=&quot;use_custom_dash&quot; v=&quot;0&quot;/>&lt;prop k=&quot;width_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; name=&quot;name&quot; value=&quot;&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option type=&quot;QString&quot; name=&quot;type&quot; value=&quot;collection&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>"/>
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
  <layerGeometryType>1</layerGeometryType>
</qgis>
